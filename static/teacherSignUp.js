function SignUp() {
    let logintips = $('.logintips')
    let username = document.getElementById('teachername').value
    let id = document.getElementById('teacherid').value
    let password = document.getElementById('teacherpassword').value
    let password2 = document.getElementById('password-repeat').value
    if(username===''||id===''||password===''||password2===''){
        logintips.html('Something is EMPTY')
        return;
    }else{
        if(password!==password2){
            logintips.html('Password not the same')
            return;
        }
    }
    var data = {
            'name':username,
            'id':id,
            'password':password
    }
    $.ajax({
        url:'/signup',
        type:"POST",
        data:JSON.stringify(data),
        success:function (res){
            if (res['code']===0){
                $('.logintips').html('success')
                setTimeout(function(){
                    window.location.href ='/'
                },1000)
            }
            else {
                $('.logintips').html(res.msg)
            }
        }
    })
}