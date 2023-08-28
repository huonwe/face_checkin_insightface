$("#selectFileReg").on("change",function(){
    let files = document.getElementById('selectFileReg').files
    let filePath = []
    for(let i = 0; i < files.length; i++){
        filePath.push(files[i].name)
    }
    $(".showFileName").html(filePath);
})

function cover_selectFile(){
    $('#selectFileReg').click();
}

async function uploadPictureForReg() {
    $('button').hide()
    let upload_btn = document.getElementsByName('btn_reg')
    // console.log(upload_btn)
    for(let i=0;i<upload_btn.length;i++){
        upload_btn[i].style.display='none'
    }
    let loading = document.getElementById('loading')
    var fileObj = document.getElementById('selectFileReg').files
    if(fileObj.length===0){
        alert("Please select img")
        $('button').show()
        return;
    }

    let margin = 5;
    loading.style.display='block';
    loading.innerText='loading';
    await faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models')

    for(let i=0;i<fileObj.length;i++){
        let reader = new FileReader();
        reader.readAsDataURL(fileObj[i])
        reader.onload=function (ev) {
            let image = new Image();
            image.src = ev.target.result;
            image.onload = async function () {
                let scale = 1;
                let max = 720;
                let canvas = document.createElement('canvas');
                let ctx = canvas.getContext('2d');
                if(this.width>max||this.height>max){
                    if(this.width > max){
                    scale = max / this.width;
                    }else{
                        scale = max / this.height;
                    }
                }
                canvas.width = this.width*scale
                canvas.height = this.height*scale
                ctx.drawImage(this,0,0,canvas.width,canvas.height);
                let detection = await faceapi.detectSingleFace(image)
                if(detection._score>=0.6){
                    ctx.drawImage(canvas,detection._box._x-margin,detection._box._y-margin,detection._box._width+margin*2,detection._box._height+margin*2,0,0,detection._box._width+margin*2,detection._box._height+margin*2)
                }
                // console.log(detection)
                let img = canvas.toDataURL('image/jpeg',0.9);
                let arr = img.split(','),
                    mime = arr[0].match(/:(.*?);/)[1],
                    bstr = atob(arr[1]),
                    n = bstr.length,
                    u8arr = new Uint8Array(n);
                while(n--){
                    u8arr[n] = bstr.charCodeAt(n);
                }
                let file = new File([u8arr],fileObj[i].name,{type:mime});
                // file.lastModified = new Date();
                let formFile = new FormData();
                formFile.append('file',file)
                // files.append(file)
                // console.log(formFile.getAll('file'))
                $.ajax({
                    url: "/register",
                    data: formFile,
                    type:'POST',
                    cache:false,
                    processData: false,
                    contentType:false,
                    success:function (result){
                        $('button').show()
                        for(let i=0;i<upload_btn.length;i++){
                            upload_btn[i].style.display='block'
                        }
                        loading.style.display='none';
                        loading.innerText='';
                        if(result['code']){
                            alert(result['msg'])
                            if(result['url']){
                                window.location.href=result['url']
                            }
                        }
                        $('#registerResult').html(result)
                    },

                })
            }
        }
        // console.log(files)
    }
}