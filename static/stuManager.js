function delStu(stu_id) {
    id = stu_id
    var r = confirm('are you sure to del '+stu_id+'?')
    if(r){
        data={
            'id':id
        }
        $.ajax({
            url:'/manager/del',
            type:'POST',
            data:JSON.stringify(data),
            beforeSend:function (xhr) {
                xhr.setRequestHeader('token',localStorage.token)
            },
            success:function (res) {
                jsonR = jsonifyRes(res)
                if(jsonR.code === 4001){
                    $('#'+id).remove()
                }else {
                    handleCode(jsonR)
                }
            },
            error:function (error) {
                console.log(error)
            }
        })
    }
}