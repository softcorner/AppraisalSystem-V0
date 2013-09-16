# Create your views here.
from django.shortcuts import render_to_response
from Login.models import UserDetails, Designation, Project, Language, Technology,Appraisment,AppraisalContent,Option
from django.contrib.sessions.models import Session
from django.template.context import RequestContext
from django.core.context_processors import csrf 
from django.http import HttpResponseRedirect 
from django.http import HttpResponse
from django.core.context_processors import csrf
from django.utils import timezone
from django.utils import simplejson
import json


def GenerateReports(request):
    args={}
    args.update(csrf(request))
    nUserID = request.session['UserID']
    objUserId = UserDetails.objects.get(user_id=request.session['UserID'])
    args['type']=objUserId.type
    if  Appraisment.objects.filter(appraisee=nUserID,appraiser=nUserID,status="Report").count() >=1 :
        AppCount = Appraisment.objects.filter(appraisee=nUserID).exclude(appraiser=nUserID).count()
        AppCompletedCount =Appraisment.objects.filter(appraisee=nUserID,status="Report").exclude(appraiser=nUserID).count()
        if  AppCount>0 and AppCompletedCount>0 and AppCount == AppCompletedCount  :    
            appraisment_list = GenerateReportList(request,nUserID)
            args['reports']=appraisment_list
            calculateFinalIndex(appraisment_list)
            if nTotalCalculation>=1:
                args['othersTotal']=(nUserCalculation /nTotalCalculation)* 100
            else:
                args['othersTotal']=0
            
            if nTotalCalculationSelf>=1:
                 args['selfTotal']=(nSelfCalculation/nTotalCalculationSelf)*100
            else:
                args['selfTotal']=0

        else :
            args['error']="Reports not rolled out."
    else:
        args['error']="Reports not rolled out."
    
    args['UserID']=  request.session['UserID']
    args['username']=request.session['UserName']
    return render_to_response('Reports/ReportList.html',args)


def GenerateReportList(request,nUserID):
    objAppUser = Appraisment.objects.get(appraisee=nUserID,appraiser=nUserID)
    objAppOthers=None

    try:
        objAppOthers = Appraisment.objects.filter(appraisee=nUserID).exclude(appraiser=nUserID)
    except:
        objAppOthers=None
    appraisment_list = []
    objQuestionUser = AppraisalContent.objects.filter(appresment=objAppUser.appraisment_id)
    for questionUser in objQuestionUser:
        appraisment = {}
        appraisment['questionID']=questionUser.question.question_id
        appraisment['header']=questionUser.question.info
        appraisment['question']=questionUser.question.question
        appraisment['status']=questionUser.question.type
        appraisment['TotalCalculation']=0
        appraisment['UserCalculation']=0
        appraisment['SelfCalculation']=0  
        appraisment['TotalCalculationSelf']=0  
        if questionUser.question.intent ==1:
            intentValue = 1
        else:
            intentValue = -1
        #Getting values for self appraisment
        if questionUser.answer!=None:
            if questionUser.question.type == 'Scale' :
                appraisment['answerYourself']=float(questionUser.answer.answer)
                appraisment['SelfCalculation']=float(int(questionUser.answer.answer)*objAppUser.appraiser.user_weight*intentValue*questionUser.question.weight)
                appraisment['TotalCalculationSelf']=float(10*objAppUser.appraiser.user_weight*intentValue*questionUser.question.weight)
            elif questionUser.question.type == 'Subjective':
                appraisment['answerYourself']=questionUser.answer.answer
            else:
                
                objoptionHeader = Option.objects.get(option_id=questionUser.answer.answer)
                
                appraisment['answerYourself']=objoptionHeader.option_id
                appraisment['SelfCalculation']=float(int(objoptionHeader.order*objoptionHeader.option_level)*objAppUser.appraiser.user_weight*intentValue*questionUser.question.weight)
                objOption =Option.objects.filter(option_header=questionUser.question.option_header)
              #  appraisment['option']=objOption
                option_list = []
                objOptionMax = Option.objects.filter(option_header=questionUser.question.option_header).order_by('-order')[0]
                
                for options in objOption:
                    option={}
                    option['option_text']=options.option_text
                    option['option_id']=options.option_id
                    option['option_level']=options.option_level
                    option['option_order']=options.order
                    option['option_count']=0
                    mcqCount=0
                    appraisment['TotalCalculationSelf']=int(objOptionMax.order*objOptionMax.option_level)*objAppUser.appraiser.user_weight*intentValue*questionUser.question.weight
                    #Calculating others appraisment values for MCQ (Need this because it has to be added with options list)
                    for questionOther in objAppOthers:
                         
                
                         try:
                             objappContent = AppraisalContent.objects.get(appresment=questionOther.appraisment_id,question=questionUser.question,answer_forbid_admin=1)
                         except:
                             objappContent=None
                         if objappContent!=None:
                             if objappContent.answer!=None:
                                 if objappContent.question.type == 'MCQ' :
                                     if str(objappContent.answer.answer) == str(options.option_id):
                                         appraisment['UserCalculation']=float(appraisment['UserCalculation']*mcqCount +float(int(options.order*options.option_level)*questionOther.appraiser.user_weight*intentValue*questionUser.question.weight))
                                         appraisment['TotalCalculation']=float((appraisment['TotalCalculation']*mcqCount+float(int(objOptionMax.order*objOptionMax.option_level)*questionOther.appraiser.user_weight*intentValue*questionUser.question.weight))/(mcqCount+1))
                                         mcqCount=mcqCount+1
                                         option['option_count']=option['option_count']+1
                    option_list.append(option)
                appraisment['options']=option_list
        count=0                        
        answerOther=''
        
        #Calculating others appraisment values for scale and subjective
        if objAppOthers!=None:
            sAnswer=''
            arrAnswerUserList=[]
            
            appraisment['answerOther']=0
            for questionOther in objAppOthers:
                try:
                    #data = AppraisalContent.objects.filter(appresment=objAppOthers.appraisment_id,question=questionUser.question).count()
                   # print data
                    objappContent = AppraisalContent.objects.get(appresment=questionOther.appraisment_id,question=questionUser.question,answer_forbid_admin=1)
                except:
                    objappContent=None
                if objappContent!=None:
                    if objappContent.answer!=None:
                        if objappContent.question.type == 'Scale' :
                            sAnswer=objappContent.answer.answer
                            appraisment['answerOther']=float((appraisment['answerOther']*count+int(sAnswer))/(count+1))
                            appraisment['UserCalculation']=float((appraisment['UserCalculation']*count +float(int(sAnswer)*questionOther.appraiser.user_weight*intentValue*questionUser.question.weight))/(count+1))
                            appraisment['TotalCalculation']=float((appraisment['TotalCalculation']*count+float(10*questionOther.appraiser.user_weight*intentValue*questionUser.question.weight))/(count+1))
                            count = count +1
                            appraisment['count']=count
                            
                        elif questionUser.question.type == 'Subjective':
                            count = count +1
                            sAnswer=sAnswer+ str(count)+') '+objappContent.answer.answer+'\n'
                            appraisment['answerOther']=sAnswer
        
        
        #Calculating the total column values for scale and MCQ type question
        if questionUser.question.type == 'Scale' :
            if questionUser.question.intent ==1:
                appraisment['total'] =   appraisment['answerOther']-appraisment['answerYourself']
            else:
                appraisment['total'] =   appraisment['answerYourself']-appraisment['answerOther']
        elif questionUser.question.type == 'MCQ' :
            selfCount = 0.0
            otherCount = 0.0
            userCount=0
            for option in appraisment['options']:
                if option['option_id'] == appraisment['answerYourself']:
                    selfCount = option['option_level']*option['option_order']
                otherCount = otherCount + float((option['option_level']*option['option_order'])*option['option_count'])
            appraisment['mcqSelfCount']=selfCount

            appraisment['mcqOtherCount']=otherCount
            if  questionUser.question.intent ==1:
                appraisment['total'] =  otherCount -selfCount
            else:
                appraisment['total'] =  selfCount - otherCount 
        
        appraisment_list.append(appraisment)    
    return appraisment_list

def calculateFinalIndex(appraismentList):
    global nSelfCalculation
    global nUserCalculation
    global nTotalCalculation
    global nTotalCalculationSelf
    nSelfCalculation=0
    nUserCalculation=0
    nTotalCalculation=0
    nTotalCalculationSelf=0
    for appraisment in appraismentList:
        if appraisment['status']!="Subjective":
            nSelfCalculation = nSelfCalculation + appraisment['SelfCalculation']
            nUserCalculation = nUserCalculation + appraisment['UserCalculation']
            nTotalCalculation = nTotalCalculation + appraisment['TotalCalculation']
            nTotalCalculationSelf =nTotalCalculationSelf+ appraisment['TotalCalculationSelf']
    
            
def adminGenerateEmployeeReports(request):
    args={}
    args.update(csrf(request))
    nUserID = request.session['UserID']
    objUserId = UserDetails.objects.get(user_id=request.session['UserID'])
    args['type']=objUserId.type
    if objUserId.type=="Administrator":
        objUsers = UserDetails.objects.filter(type="Employee")
        if request.POST:
            #print '--------------'
            if request.POST['drpUser']!='0':
                userID = int(request.POST['drpUser'])
             #   print Appraisment.objects.filter(appraisee=userID,appraiser=userID,status="Completed").count()
                if  Appraisment.objects.filter(appraisee=userID,appraiser=userID,status="Completed").count() >=1 :
                    AppCount = Appraisment.objects.filter(appraisee=userID).exclude(appraiser=userID).count()
                    AppCompletedCount =Appraisment.objects.filter(appraisee=userID,status="Completed").exclude(appraiser=userID).count()
                    if AppCount == AppCompletedCount :    
                        appraisment_list=GenerateReportList(request, request.POST['drpUser'])
                        args['reports']=appraisment_list
                        calculateFinalIndex(appraisment_list)
                        if nTotalCalculation>=1:
                            args['othersTotal']=(nUserCalculation /nTotalCalculation)* 100
                        else:
                            args['othersTotal']=0
                        
                        if nTotalCalculationSelf>=1:
                             args['selfTotal']=(nSelfCalculation/nTotalCalculationSelf)*100
                        else:
                            args['selfTotal']=0

                    else :
                        args['error']="Appraisal not completed for selected user"
                else:
                    args['error']="Self appraisal not completed"
            else:
                args['error']="Please select user"
            args['UserID']=  request.session['UserID']
            args['username']=request.session['UserName']
            args['UserList']=objUsers
            args['drpUser']=int(request.POST['drpUser'])
            return render_to_response('Reports/ReportList.html',args)
        else:
            args['UserID']=  request.session['UserID']
            args['username']=request.session['UserName']
            args['UserList']=objUsers
            return render_to_response('Reports/ReportList.html',args)
    else:
        args['UserID']=  request.session['UserID']
        args['username']=request.session['UserName']
        args['error']="Not valid user"
        return render_to_response('Reports/ReportList.html',args)

    
def IndividualQuestionDetails(request):
      if request.is_ajax():
        nQuestionID = request.POST.get('QuestionID')
        nUserID = request.POST.get('UserID')
        objAppOthers = Appraisment.objects.filter(appraisee=nUserID).exclude(appraiser=nUserID)
        arrQuestionList=[]
        for appOther in objAppOthers:
           try:
               objappContent = AppraisalContent.objects.get(appresment=appOther.appraisment_id,question=nQuestionID)
           except:
               objappContent=None
           if objappContent:
               lstQuestionList={}
               lstQuestionList['AppraisalContentID']=objappContent.appraisal_content_id
               lstQuestionList['appresmentID']=appOther.appraisment_id
               lstQuestionList['UserName']=appOther.appraiser.firstname
               lstQuestionList['answer_forbid_admin']=objappContent.answer_forbid_admin
               if objappContent.question.type != 'MCQ':
                   lstQuestionList['answer']=objappContent.answer.answer
               else:
                   lstQuestionList['answer']=Option.objects.get(option_id=objappContent.answer.answer).option_text     
               arrQuestionList.append(lstQuestionList)
        data= json.dumps(arrQuestionList) 
        return HttpResponse(content=data, content_type='json')
        #//objOptions = OptionHeader.objects.get(option_header_id=search_text);
        #//result =''
        #//for option in objOptions.option_set.filter():
       # //    result+= option.option_text + '|'+ str(option.option_level) +','
       
        #data = simplejson.dumps(arrQuestionList)
        #data =json.dumps(arrQuestionList)
        #return HttpResponse(content=data, content_type='json')
        
        
def AnswerForbidUpdate(request):
    flag=False
    if request.is_ajax():
        try:
            sAnswerForbid = request.POST.get('AnswerForbid')
            arrAnswerForbid = sAnswerForbid.split(",")
            for index, sAnswer in enumerate(arrAnswerForbid):
                 arrSplitForbidNID = sAnswer.split("|")
                 AppraisalContent.objects.filter(appraisal_content_id=arrSplitForbidNID[0]).update(answer_forbid_admin=arrSplitForbidNID[1],modified_on=timezone.now())
            flag=True
        except:
            flag=False     
    if flag:
        objResponse = {'success':'Records updated'}
    else:
        objResponse = {'error':'Error occurred while updating'}
    
    data = simplejson.dumps(objResponse)
         
    return HttpResponse(content=data, content_type='json')
                
