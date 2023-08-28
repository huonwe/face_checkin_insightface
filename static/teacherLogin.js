function Login() {
    id = document.getElementById('id').value
    password = document.getElementById('password').value
    if(id === '' || password === ''){
        $('.logintips').html('YOU HAVE NOT INPUT CID OR PASSWORD')
        return;
    }

    var data = {
        'id':id,
        'password':password
    }
    $.ajax({
        url:'/login',
        type:"POST",
        data:JSON.stringify(data),
        success:function (res){
            if(res === 'success'){
                window.location.href='/home'
            }
            else {
                $('.logintips').html('CID OR PASSWORD INCORRECT')
            }
        }
    })

}