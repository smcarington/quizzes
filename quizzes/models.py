from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

# Row based permissions
from guardian.models import UserObjectPermission

class Course(models.Model):
    """ A container for storing multiple quizzes. Will only be visible to students
        who are enrolled in that course.
    """
    name = models.CharField(max_length=20)
    # Allows any student to enroll
    open_enrollment = models.BooleanField(default=False) 
    # Determine whether a quiz is live or not.
    status = models.BooleanField(blank=True, default=False)

    def update_last_active(self):
        self.last_active = timezone.now()
        self.save()

    def add_admin(self, username):
        """ Adds row level adminstrative abilities for the specified user. Takes
        an optional parameter 'staff' (default False) which indicates whether
        the user is staff or admin. Admin have the permission 'can_edit_poll'
        while staff have 'can_see_poll_admin'.
        """
        try:
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.save()

            # Make sure the user is also a part of the course
            membership, _ = UserMembership.objects.get_or_create(user=user)
            membership.courses.add(self)

            # Give the user permission to edit this course
            perm = 'can_edit_quiz'
            UserObjectPermission.objects.assign_perm(
                perm, user, obj=self
            )
        except Exception as e:
            print(e)

    def get_status(self):
        return self.status

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ("can_edit_quiz", "Can edit the quiz"),
        )

class UserMembership(models.Model):
    """ Tracks which courses a student/ta can see. General use should be to get
    a UserMembership object according to user, then the um.courses.add(course)
    command.
    """
    user = models.ForeignKey(User)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        course_string = ''
        for course in self.courses.all():
            course_string += str(course)

        return "{}: {}".format(
            self.user.username,
            course_string)


class Quiz(models.Model):
    """ Container for holding a quiz. Quizzes consist of several MarkedQuestion
        objects. In particular, a Quiz object has the following attributes:
        name - (CharField) the name of the quiz
        tries - (IntegerField) The number of attempts a student is permitted to
            for the quiz. A value of tries=0 means unlimited attempts
        live  - (DateTimeField) The date on which the quiz becomes available to
            students
        expires - (DateTimeField) The date on which the quiz closes. 
        out_of - (IntegerField) The number of different MarkedQuestion pools. 
    """
    name    = models.CharField("Name", max_length=200)
    # Number of tries a student is allowed. A value of category=0 is equivalent to infinity.
    tries   = models.IntegerField("Tries", default=0)
    live    = models.DateTimeField("Live on")
    expires = models.DateTimeField("Expires on")
    out_of  = models.IntegerField("Points", default=1)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def update_out_of(self):
        """ Determines the number of MarkedQuestion pools in this quiz. Is
            called when MarkedQuestions are added/edited/deleted from the quiz
        """
        # Important to base this on the max category, rather than number of questions
        self.out_of = self.markedquestion_set.aggregate(Max('category'))['category__max']
        if not self.out_of: # New quiz, so markedquestion_set is empty
            self.out_of = 0
        self.save()

    def get_random_question(self, category):
        """ Returns a random question with foreign key (self) and the given category
            Input: category (integer) - the MarkedQuestion pool to take from
            Output: (MarkedQuestion) object
        """
        
        return random.choice(self.markedquestion_set.filter(category=category))

    def __str__(self):
        return self.name

class MarkedQuestion(models.Model):
    """ An instance of a question within a Quiz object. These are designed to
        have randomized inputs, and additionally can be assigned to a
        MarkedQuestion pool. For example, if three questions all belong to the
        same pool, then when a quiz is created, only one of these three
        questions will be chosen.
        quiz - (ForeignKey[Quiz]) The quiz to which the MarkedQuestion belongs
        category (IntegerField) The MarkedQuestion pool
        problem_str - (TextField) The question itself. Generated variables
            should be the form {v[0]}, {v[1]},..., etc. Should take LaTeX with
            delimiters \( \), though this looks horrific when escaped.
        num_vars - (IntegerField) Keeps track of the number of variables within
            the question
        choices - (TextField) The range that the variables are allowed to take
            on. Delimited by a colon.
        answer - (TextField) The correct answer. Should include {v[0]}, {v[i]}
            as well.
        functions - (TextField) User defined functions.
        q_type - (CharField) Can either be direct entry 'D' (student puts in a
            number) or multiple choice 'MC'. True/False is deprecated as it can
            be created with MC.
        mc_choices - (TextField) Used only when q_type = 'MC', and includes the
           multiple choice answers. These can include variables {v[i]} as well,
           and are delimited by a semi-colon.
    """
    quiz        = models.ForeignKey("Quiz", Quiz, null=True)
    # Keeps track of the global category, so that multiple questions can be used
    category    = models.IntegerField("Category", default=1)
    problem_str = models.TextField("Problem")
    choices     = models.TextField("Choices", null=True)
    num_vars    = models.IntegerField(null=True)
    answer      = models.TextField("Answer")
    functions   = models.TextField("Functions", default='{}')
    # Allows for multiple kinds of questions
    QUESTION_CHOICES = ( 
            ('D', 'Direct Entry'),
            ('MC', 'Multiple Choice'),
            ('TF', 'True/False'),
        )

    q_type      = models.CharField("Question Type",
                    max_length=2, 
                    choices=QUESTION_CHOICES,
                    default='D',
                  )
    mc_choices = models.TextField("Multiple Choice", default ='[]', blank=True)

    class Meta:
        ordering = ['quiz', 'category']
        verbose_name = "Marked Question"

    def update(self, quiz):
        """ Updates the quiz to which this belongs, and updates that quiz's
            attributes as well. Called when adding/editing/deleting a
            MarkedQuestion.
        """
        self.quiz = quiz
        self.num_vars = len(re.findall(r'{v\[\d+\]}', self.problem_str))
        self.save()
        quiz.update_out_of()

    def get_random_choice(self):
        """ Returns a random choice"""
        return random.choice(self.choices.split(':'))

    def __str__(self):
        return self.problem_str


class StudentQuizResult(models.Model):
    """ When a student starts/writes a quiz, it creates a StudentQuizResult
        instance. This tracks which questions were generated in the quiz, which
        choices for the variables were made, how the student answered (both the
        direct input and how it was evaluated). 
        <<Attributes>>
        student - (ForeignKey[User]) The student who wrote the quiz
        quiz    - (ForeignKey[Quiz]) The quiz the student wrote
        attempt - (IntegerField) Which attempt does this StudentQuizResult
            correspond to.
        cur_quest - (IntegerField) This object is updated each time the student
            completes a question. This tracks which question the student is on,
            allowing the student to leave during a quiz and resume again later.
        result - (TextField) String serialized as a JSON object. 
        score - (IntegerField) The score the student achieved in this question.
    
    """
    student   = models.ForeignKey(User)
    quiz      = models.ForeignKey(Quiz)
    attempt   = models.IntegerField(null=True, default=1) #track which attempt this is
    #track which question the student is on if they leave. If cur_question = 0 then completed
    cur_quest = models.IntegerField(null=True, default=1) 

    # The result is a json string which serializes the question data. For example
    # result = {
    #           '1': {
    #                   'pk': '13',
    #                   'inputs': '1;2;3', 
    #                   'score': '0',
    #                   'answer': 22.3,
    #                   'guess_string': '-22.3*cos(pi)',
    #                   'guess': 15.7,
    #                   'type': 'D',
    #                 },
    #           '2': {
    #                   'pk: '52'
    #                   'inputs': '8;-2', 
    #                   'score': '1',
    #                   'answer': 3.226,
    #                   'guess': '3.226',
    #                   'guess_string': '3.226',
    #                   'type': 'MC',
    #                   'mc_choices': ['3.226', '14', '23', '5.22'],
    #                 },
    #          }
    #          Indicates that the first question is a MarkedQuestion with pk=13, the inputs to
    #          this question were v=[1,2,3], and the student got the question wrong with a guess of 15.7
    result  = models.TextField(default='{}')
    score   = models.IntegerField(null=True)

    class Meta:
        verbose_name = "Quiz Result"

    def update_score(self):
        """ Adds one to the overall score """
        self.score += 1
        self.save()

    def update_result(self, result):
        """ Takes a python dictionary, serializes it, and stores it in the result column.
            Input: result (dict) - the python dictionary.
            Output: Void
        """
        self.result = json.dumps(result)
        self.save()

    def get_result(self):
        """ Returns a python dictionary with the student quiz results
            Input: None
            Output: result (dict) - The python dictionay of results
                    attempt (string) - The current attempt, as a string to access in result
        """
        result = json.loads(self.result)
        attempt = str(self.cur_quest)
        return result, attempt

    def add_question_number(self):
        """ Adds one to the cur_quest field. However, checks if we have surpassed the last question,
            and if so sets cur_quest to 0.
            Input: None
            Output: is_last (Boolean) - indicated whether the cur_quest field has been set to 0
            TODO: Change this to allow for non-sequential numbering of
                  categories
        """
        num_quests = self.quiz.out_of
        if self.cur_quest == num_quests:
            is_last = True
            self.cur_quest = 0
        else:
            is_last = False
            self.cur_quest += 1
        self.save()
        
        return is_last

    def __str__(self):
        return self.student.username + " - " + self.quiz.name + " - Attempt: " + str(self.attempt)


class CSVFile(models.Model):
    """ Used for storing CSV files.
    """
    doc_file  = models.FileField(upload_to="tmp/")

    def __str__(self):
        return self.doc_file
