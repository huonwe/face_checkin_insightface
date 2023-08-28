function openSidebar(){
    let Sidebar = $("#Sidebar");
    let LeftContainer = $(".LeftContainer")
    // $("#Sidebar").animate({left:'25%'});
    if(Sidebar[0].style.left==='-10em'){
        Sidebar.animate({left:'0%',width:'5em'});
        LeftContainer.animate({width:'5em'})
    }else{
        Sidebar.animate({left:'-10em',width:'0em'})
        LeftContainer.animate({width:'0em'})
    }
}



function getRegister() {
    $.ajax({
        url:'/register',
        type:'GET',
        dataType:'html',
        success:function (res){
            let jsonR
            try{
                jsonR = JSON.parse(res)
            }catch (e){
                $('#RightContainer').html('loading')
                $('#RightContainer').html(res)
                return;
            }
            handleCode(jsonR)
        }
    })
}

function getManager() {
    $.ajax({
        url:'/manager',
        type:'GET',
        dataType:'html',
        success:function (res) {
            // console.log(res)
            let jsonR
            try{
                jsonR = JSON.parse(res)
            }catch (e){
                // console.log(res)
                $('#RightContainer').html('loading')
                $('#RightContainer').html(res)
                return;
            }
            if(jsonR.code===4002){
                console.log('aa')
                $('#RightContainer').html("<div class='empty_result_show'>"+jsonR.msg+"</div>")
            }
        },
        error:function (error) {
            console.log(error)
        }
    })
}

function getRWP() {
    $.ajax({
        url: '/recognitionWithPicture',
        type: 'GET',
        dataType:'html',
        success:function (res) {
            let jsonR
            try{
                jsonR = JSON.parse(res)
            }catch (e){
                $('#RightContainer').html('loading')
                $('#RightContainer').html(res)
                return;
            }
            handleCode(jsonR)
        },
        error:function (error) {
            console.log(error)
        }
    })
}

function getCheckin() {
    $('RightContainer').html('Loading models')



    $.ajax({
        url:'/CheckInWithCamera',
        type:'GET',
        dataType:'html',
        success:function (res) {
            let jsonR
            try{
                jsonR = JSON.parse(res)
            }catch (e){
                $('#RightContainer').html('loading')
                $('#RightContainer').html(res)
                return;
            }
            handleCode(jsonR)
        }
    })

}

