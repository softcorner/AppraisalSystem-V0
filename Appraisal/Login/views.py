# Create your views here.
from django.shortcuts import render_to_response
from django.contrib.sessions.models import Session
from models import UserDetails   
from forms import LoginForm
from django.http import HttpResponseRedirect 
from django.core.context_processors import csrf
#from Questionare.models import Login


def login(request):
    args={}
    args.update(csrf(request))
    if request.POST:
        form = LoginForm(request.POST)
        args['form']=form
        if form.is_valid():
            #flag=UserDetails.objects.filter(firstname=request.POST['txtUserName'],password=request.POST['txtPassword']).exists()
            sUserID = form.Authenticate()
            if sUserID != 0:
                args['username']= request.POST['txtUserName']
                request.session['UserID']=sUserID
                request.session['UserName']=request.POST['txtUserName']
                
                if checkIfAdmin(sUserID):
                    return render_to_response('Welcome.html',args)
                else :
                    return HttpResponseRedirect("/userprofile/Authenticate/") 
            else :
               args['error']='Not Valid user'
               return render_to_response('Login.html',args)    
        else:
            return render_to_response('Login.html',args)
            
    else:  
        objLoginForm = LoginForm()
        args['form']=objLoginForm
        return render_to_response('Login.html', args)        

def checkIfAdmin(sUserID):
        bFlag =False
        try:
            objUserDetails = UserDetails.objects.get(user_id=sUserID)
            print '---------------'
            print sUserID
            if objUserDetails.type == "Administrator":
                bFlag=True
        except UserDetails.DoesNotExist:
            bFlag =False
        
        return bFlag
    

def homeScreen(request):
    args={}
    args.update(csrf(request))
    args['username']=request.session['UserName']
    if checkIfAdmin(request.session['UserID']):
        return render_to_response('Welcome.html',args)
    else :
        return HttpResponseRedirect("/userprofile/") 
         
def logout(request):
    args={}
    if 'UserID' in request.session:
        del request.session['UserID']
        args['success']='Logout Successfully'
  # del request.session['Password']
    args.update(csrf(request))
    objLoginForm = LoginForm()
    args['form']=objLoginForm
    return render_to_response('Login.html',args)
     