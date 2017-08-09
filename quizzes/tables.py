from django_tables2 import tables, Column, Table

from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from django_tables2 import RequestConfig

from .models import *

class MathColumn(Column):
    # Records are MarkedQuestions
    def render(self, value, record):
        return format_html('<span class="mathrender">{}</span><br><small><a href="{}">(Edit)</a><a href="{}">(Delete)</a>', 
                mark_safe(value), 
                reverse('edit_quiz_question', 
                    kwargs={
                        'course_pk': record.quiz.course.pk,
                        'quiz_pk': record.quiz.pk,
                        'mq_pk': record.pk,
                    }
                ),
                reverse('delete_item', kwargs={'objectStr':'markedquestion', 'pk': record.pk}),
           )

#class LinkColumn(Column):
#    def render(self, record, value):
##        return format_html('<a href="{}">Edit Choices</a>', reverse('edit_choices', args=('1',)))
#        return format_html('{}', args=(record.id,))

class MarkedQuestionTable(Table):
    # Record is a MarkedQuestion
    problem_str = MathColumn()
    choices = Column(empty_values=())
    test = Column(empty_values=())
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'choices']

    def render_choices(self, value, record):
        return format_html('<a href={}>Edit Choices</a>', 
                reverse('edit_choices', 
                    kwargs={ 
                        'mq_pk': record.pk,
                        'quiz_pk': record.quiz.pk,
                        'course_pk': record.quiz.course.pk,
                    }
                ) 
            )

    def render_test(self,value,record):
        return format_html('<a href={}>Test</a>', 
                reverse('test_quiz_question', 
                    kwargs={
                        'mq_pk':record.pk,
                        'quiz_pk': record.quiz.pk,
                        'course_pk': record.quiz.course.pk,
                    }
                ) 
            )

class AllQuizTable(Table):
    class Meta:
        model = Quiz
        attrs = {'class': 'paleblue'}
        exclude = ['course','id']

    def render_tries(self, value, record):
        # Returns the value or infinity if value is 0
        return value or format_html('&infin;')

    def render_name(self, value, record):
        return format_html('<a href={}>{}</a>', 
            reverse('quiz_admin', 
                kwargs={'quiz_pk': record.pk,
                        'course_pk': record.course.pk}
            ), value 
        )

class SQRTable(Table):
    quiz      = Column("Quiz")
    attempt   = Column("Attempt")
    cur_quest = Column("Question")
    score     = Column("Score")
    details   = Column("Details", empty_values=(), orderable=False)

    class Meta:
        model = StudentQuizResult
        attrs = {'class': 'paleblue'}
        fields = ['quiz', 'attempt', 'cur_quest', 'score']

    def render_cur_quest(self, value, record):
        if value == 0:
            return "Completed"
        else:
            return value

    def render_details(self, value, record):
        return format_html('<a href="{}">Details</a>', 
            reverse('quiz_details', 
                kwargs={
                    'sqr_pk': record.pk, 
                    'quiz_pk': record.quiz.pk,
                    'course_pk': record.quiz.course.pk,
                }
            )
        )

class QuizResultTable(Table):
    q_num   = Column(verbose_name="Question")
    correct = Column(verbose_name="Correct Answer")
    guess   = Column(verbose_name="Your Answer")
    score   = Column(verbose_name="Score")

    class Meta:
        attrs = {'class': 'paleblue'}
        order_by = 'q_num'

    def render_correct(self, value, record):
        return format_html('<span class="mathrender">{}</span>', value)

    def render_guess(self, value, record):
        return format_html('<span class="mathrender">{}</span>', value)
