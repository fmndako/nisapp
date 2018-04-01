# -*- coding: utf-8 -*-
"""
Created on Friday Mar 2 17:29:10 2018

@author: fmndako
"""
from django.shortcuts import render, get_object_or_404, redirect

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.conf import settings
# from django.core.files import File
# from django.core.files.base import ContentFile
from django.db.models import Count

import os
from django.core.files.storage import FileSystemStorage
from django.forms import modelformset_factory
from .forms import CommentForm

from .models import Standards, ICSField, ICSGroup, ICSSubgroup, Comment
#from visits.models import counter
from django.db.models import F
import time
SUBJECTS =  {"Food / Codex": 1, "Chemical / Petroleum": 3, "Mechanical": 6, "Building / Civil": 2, "Electrical / Electronics": 5,
                "Textile / Leather": 4, "Service Standards": 7}

path = settings.MEDIA_ROOT
#{{ standard.foreword_file.url }}

def number_of_standards_updater():
    """gets number of stds per groups and updates database"""
    # ics_field_lists = ICSField.objects.order_by('ics')
    # for field_obj in ics_field_lists:
    #     #print(field_obj.ics)
    #     # each field obj has many group obj
    #     ics_group_lists = field_obj.icsgroup_set.all()
    #     # field_obj contains (len(ics_group_lists)) group objs
    #
    #     field_std_num = 0
    #     for grp_obj in ics_group_lists:
    #
    #         #print(grp_obj.ics)
    #         #time.sleep(1)
    #         #each group obj has many subgroup obj or standards obj
    #         ics_subgroup_lists = grp_obj.icssubgroup_set.all()
    #         #if group obj has no subgroup obj, then it has std obj
    #         grp_std_num = 0
    #         if len(ics_subgroup_lists) == 0:
    #             #gets stds directly under group
    #             standard_list= grp_obj.standards_set.all()
    #             std_num = len(standard_list)
    #             grp_std_num += std_num
    #         else:
    #             # each group obj has many subgroup obj
    #             for subgroup_obj in ics_subgroup_lists:
    #                 standard_list = subgroup_obj.standards_set.all()
    #                 subgroup_std_num = len(standard_list)
    #                 #print(subgroup_obj.ics, ":", subgroup_std_num)
    #                 grp_std_num += subgroup_std_num
    #                 subgroup_obj.update_number(subgroup_std_num)
    #         #print(grp_obj.ics, ":", grp_std_num)
    #         field_std_num += grp_std_num
    #         grp_obj.update_number(grp_std_num)
    #     print(field_obj.ics, ":", field_std_num)
    #     field_obj.update_number(field_std_num)

    def updater(mdl):
        objs = mdl.objects.all()
        for obj in objs:
            if mdl == ICSField:
                std = Standards.objects.filter(field_id = obj.id)
            elif mdl == ICSGroup:
                std = Standards.objects.filter(group_id=obj.id)
            else:
                std = Standards.objects.filter(subgroup_id=obj.id)
            obj.update_number(len(std))
    mdl = (ICSField, ICSGroup, ICSSubgroup)
    for i in mdl:
        updater(i)

class Counter():
    """counter class for counting object"""
    count = 0

    def increment(self):
        """increases count"""
        self.count += 1
        return ''

    def decrement(self):
        """decreases count"""
        self.count -= 1
        return ''

    def double(self):
        """doucles count"""
        self.count *= 2
        return ''

def new_index(request):
    dept = Standards.objects.values("subject").annotate(dcount=Count("subject"))
    context = {"subjects": dept}
    return render(request, "nisapp/new_index.html", context)
def index(request):
    """returns a simple html"""
    #number_of_standards_updater()
    print(path)
    ics_field_lists = ICSField.objects.order_by('-numbers')
    field_url = "nisapp:fields"
    page_name = "ICS Fields"
    context = {"ics_field_lists": ics_field_lists, "field_url": field_url,
               "page_name": page_name, "count": Counter() }
    return render(request, "nisapp/index.html", context)


def search(request):
    """handles the search event, looks up db and then returning a response"""
    #bad way
    #print request.GET["q"]
    #accepted way
    print request.GET.get("q")
    query = request.GET.get('q')
    result = Standards.objects.all()
    if query:
        #query_list = query.split()
        result = result.filter(title__icontains=query)
    else:
        result = ["No results"]
    return render(request, "nisapp/index.html", {"standards_list" : result, "search": query})

def mydetail(request, pk):
    """loads detail html for the Standards with pk"""
    # ##for visits
    # AuthorFormSet = modelformset_factory(Comment, fields=('name',), max_num=1)
    # formset = AuthorFormSet(queryset=Comment.objects.order_by('name'))
    standards = get_object_or_404(Standards, pk=pk)
    comment = Comment.objects.filter(standard = standards, active=True, parent__isnull=True)
    if standards.subgroup_id != None:
        print("sub")
        similar_standards = Standards.objects.filter(
                subgroup_id=standards.subgroup_id).exclude(
                        pk=pk)

    elif standards.group_id != None:
        print("Grp")
        similar_standards = Standards.objects.filter(
        group_id=standards.group_id).exclude(
                        pk=pk)
    elif standards.field_id != None:
        print("field")
        similar_standards = Standards.objects.filter(
                field_id=standards.field_id).exclude(
                        pk=pk)
    else:
        similar_standards = []

    if not standards.foreword_file and len(standards.foreword) > 43: pass
    # if request.method == "POST":
    #     form = CommentForm(request.POST)
    #     if form.is_valid():
    #         post = form.save(commit=False)
    #         post.standard = standards
    #         #post.published_date = timezone.now()
    #         post.save()
    #         return HttpResponseRedirect(reverse('nisapp:detail', args=(standards.id,)))
    # else:
    #     form = CommentForm()
    if request.method == 'POST':
        # form has been added
        form= CommentForm(request.POST)
        if form.is_valid():
            parent_obj = None
            # get parent form id from hidden input
            try:
                # id integer e.g. 15
                parent_id = int(request.POST.get('parent_id'))
            except:
                parent_id = None
            # if parent_id has been submitted get parent_obj id
            if parent_id:
                parent_obj = Comment.objects.get(id=parent_id)
                # if parent object exist
                if parent_obj:
                    # create replay form object
                    replay_comment = form.save(commit=False)
                    # assign parent_obj to replay form
                    replay_comment.parent = parent_obj
            # normal form
            # create form object but do not save to database
            new_comment = form.save(commit=False)
            # assign the standard as comments foreignkey
            new_comment.standard = standards
            # save
            new_comment.save()
            return HttpResponseRedirect(reverse('nisapp:detail', args=(standards.id,)))
    else:
        form= CommentForm()


    return render(request, "nisapp/detail.html", {
                                'standard':standards,
                                "similar_standard": similar_standards, "formset": form, "comments": comment})

def fields(request, pk):
    """handles views of all groups with field_id = pk"""
    ics_group_lists = ICSGroup.objects.filter(field_id=pk)
    field_url = "nisapp:groups"
    page_name = "ICS Group"
    context = {"ics_field_lists": ics_group_lists, "field_url": field_url,
               "page_name": page_name, "count": Counter()}
    return render(request, "nisapp/index.html", context )

def groups(request, pk):
    """handles views of all subgroups withgroup_id = pk"""
    field_url = "nisapp:subgroups"
    page_name = "ICS Subgroup"
    ics_group_lists = ICSSubgroup.objects.filter(group_id=pk)

    if len(ics_group_lists) != 0:
        print("subgroup available")
        context = {"ics_field_lists": ics_group_lists, "field_url": field_url,
                   "page_name": page_name, "count": Counter()}
        return render(request, "nisapp/index.html", context)
    else:
        print("not available")
        field_url = "nisapp:detail"
        page_name = "standards"

        standards_lists = Standards.objects.filter(group_id = pk)
        print(len(standards_lists))
        context = {"ics_field_lists": standards_lists, "field_url": field_url,
                   "page_name": page_name, "count": Counter()}
        return render(request, "nisapp/index.html", context)

def subgroups(request, pk):
    """handles views of all standards with subgroups = pk"""
    field_url = "nisapp:detail"
    page_name = "Standards"
    standards_lists = Standards.objects.filter(subgroup_id = pk)
    # print(len(standards_lists))
    context = {"ics_field_lists": standards_lists, "field_url": field_url,
               "page_name": page_name, "count": Counter()}
    return render(request, "nisapp/index.html", context)

def standards(request, group, ics):
    """handles numbers click on all groups list, field_url: url to go to onclick,
    page_name: name of page,counter() class handles S/N"""
    print(group, ics)
    ics = int(ics)
    if str(group) == "ICS Fields":
        standards_lists = Standards.objects.filter(field_id = ics)
    elif str(group) == "ICS Group":
        standards_lists = Standards.objects.filter(group_id = ics)
    elif str(group) == "ICS Subgroup":
        standards_lists = Standards.objects.filter(subgroup_id = ics)
    else:
        standards_lists = []
    field_url = "nisapp:detail"
    page_name = "standards"
    context = {"ics_field_lists": standards_lists, "field_url": field_url,
               "page_name": page_name, "count": Counter()}
    return render(request, "nisapp/index.html", context)

def aspect(request, text):
    """handles views of standard by aspect type"""
    nis = ["NIS", "DNIS"]
    ncp = ["NCP", "DNCP"]
    if text == "nis":
        lists = nis
        print(lists)
    elif text == "ncp":
        lists = ncp

    else:
        lists = nis + ncp

    aspect_lists = []
    for i in lists:
        aspect_lists += Standards.objects.filter(designation__exact=i)

        # for i in org:
        #     aspect_lists = Standards.objects.exclude(designation__exact="NIS")
    context = {"standard_list": aspect_lists, "len": len(aspect_lists),
               "page_name": text, "count": Counter()}
    return render(request, "nisapp/aspect.html", context)

def foreword():
    """creates a foreword.txt in static media and"""
    pass

def post_detail(request, post):
    # get post object
    post = get_object_or_404(Post, slug=post)
    # list of active parent comments
    comments = post.comments.filter(active=True, parent__isnull=True)
    if request.method == 'POST':
        # comment has been added
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            parent_obj = None
            # get parent comment id from hidden input
            try:
                # id integer e.g. 15
                parent_id = int(request.POST.get('parent_id'))
            except:
                parent_id = None
            # if parent_id has been submitted get parent_obj id
            if parent_id:
                parent_obj = Comment.objects.get(id=parent_id)
                # if parent object exist
                if parent_obj:
                    # create replay comment object
                    replay_comment = comment_form.save(commit=False)
                    # assign parent_obj to replay comment
                    replay_comment.parent = parent_obj
            # normal comment
            # create comment object but do not save to database
            new_comment = comment_form.save(commit=False)
            # assign ship to the comment
            new_comment.post = post
            # save
            new_comment.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        comment_form = CommentForm()
tima = ''' 
class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

def myloader_index(request):
    """uses loader from django.template to augment httpresponse"""
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template("polls/index.html")
    context = {"latest_question_list":latest_question_list}
    return HttpResponse(template.render(context, request))

def myindex(request):
    """uses render from django.shortcuts to render a template"""
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {"latest_question_list":latest_question_list}
    return render(request, "polls/index.html", context)    

def mydetail(request, question_id):
    
    ##for visits
    question = get_object_or_404(Question, pk=question_id)
    try:
        # counts = counter.objects.get(question= question_id)
        # counts.count =  F("count")+1
        # ###counts.count +=1 #used instead of F(), F is prefered to avoid race condition
        # counts.save()
        # counts.refresh_from_db()
        # print counts.count
        ###the above expresssions can be simplified using update(get() and save()
        counts = counter.objects.filter(question = question_id)
        counts.update(count=F('count')+1)
        
        ###update all
        #counter.objects.all().update(count=F('count') + 1)
        
        
    except: 
        counts = counter(count = 1, question = question_id)
        counts.save()
    
    counts = counter.objects.get(question = question_id)
    return render(request, "polls/detail.html", {
                                            'question':question, 
                                            "count" : counts.count
                                            })
                                       
def listviewer(request):
    """simple querying"""
    ministry = Ministry.objects.all()
    
    return render(request, "polls/listviewer.html", {"value":ministry})
                                            
def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    documents = Docs.objects.all()
    return render(request, 'polls/results.html', {'question': question, "documents" : documents})
    
def vote(request, question_id):
    #print request.POST["myname"]
    question = get_object_or_404(Question, pk=question_id)
    newdoc = Docs(docfile = request.FILES["pic"])
    print request.FILES["pic"]._size
    
    newdoc.save()
    print "here", newdoc.id
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
        try:
            newdoc = Docs(docfile = request.FILES["pic"])
            statinfo = os.stat("newdoc")
            print statinfo
            print statinfo.st_size
            
            newdoc.save()
            print "here", newdoc.id
        except:
            pass
    except (KeyError, Choice.DoesNotExist):
        return render(request, "polls/detail.html", {
                        "question" :question,
                        "error_message" : "You didn't select a choice.",
                        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
           # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
        
def picture(request, question_id):
    try:
        #newdoc = Docs(docfile = request.FILES["pic"])
        
        myid = 12
        #newdoc.save()
        #myid =  newdoc.id
    except:
        print "no file attached"
        return render(request, "polls/index.html", {
                        "error_message" : "You didn't input a picture.",
                        })
    print request.POST["myname"], question_id
    documents = get_object_or_404(Docs, pk = 4)
    print documents.docfile
    return render(request, "polls/index.html", {"documents": documents})'''

