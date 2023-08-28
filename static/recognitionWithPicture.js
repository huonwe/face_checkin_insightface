$("#hidden_selectFileBtn").on("change",function(){
    let files = document.getElementById('hidden_selectFileBtn').files
    let filePath = []
    for(let i = 0; i < files.length; i++){
        filePath.push(files[i].name)
    }
    $(".showFileName").html(filePath);
})

function call_selectFile(){
    $('#hidden_selectFileBtn').click();
}
async function uploadPictureForRecognition() {
    $('button').hide()
    $('#div-result').html('')
    // $('.upload_file_form').hide()
    let margin = 5;
    let loading = document.getElementById('loading')
    loading.style.display = 'block';
    loading.innerText = 'loading';
    await faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models')


    let files = document.getElementById('hidden_selectFileBtn').files
    if (files.length === 0) {
        alert("Please select img")
        loading.style.display = 'none';
        $('button').show()
        return;
    }

    await faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models')

    for(let i=0;i<files.length;i++){
        let reader = new FileReader();
        reader.readAsDataURL(files[i])
        reader.onload=function (ev) {
            let image = new Image();
            image.src = ev.target.result;
            let formFile = new FormData();
            image.onload = async function () {
                let scale = 1;
                let max = 720;
                let canvas = document.createElement('canvas');
                let canvas_crop = document.createElement('canvas');
                let ctx = canvas.getContext('2d');
                let ctx_crop = canvas_crop.getContext('2d')
                if(this.width>max||this.height>max){
                    if(this.width > max){
                    scale = max / this.width;
                    }else{
                        scale = max / this.height;
                    }
                }
                canvas.width = this.width*scale
                canvas.height = this.height*scale
                canvas_crop.width = 160
                canvas_crop.height = 160
                ctx.drawImage(this,0,0,canvas.width,canvas.height);

                let detection = await faceapi.detectAllFaces(image)
                for(let j=0;j<detection.length;j++){
                    ctx_crop.clearRect(0,0,canvas.width,canvas.height)
                    ctx_crop.drawImage(canvas,detection[j]._box._x-margin,detection[j]._box._y-margin,detection[j]._box._width+margin*2,detection[j]._box._height+margin*2,0,0,canvas_crop.width,canvas_crop.height)

                    // console.log(detection)
                    let img = canvas_crop.toDataURL('image/jpeg',0.9);
                    let arr = img.split(','),
                        mime = arr[0].match(/:(.*?);/)[1],
                        bstr = atob(arr[1]),
                        n = bstr.length,
                        u8arr = new Uint8Array(n);
                    while(n--){
                        u8arr[n] = bstr.charCodeAt(n);
                    }
                    let file = new File([u8arr],{type:mime});
                    // file.lastModified = new Date();

                    formFile.append('file',file)
                    // files.append(file)
                    // console.log(formFile.getAll('file'))
                }
                $.ajax({
                    url: "/recognitionWithPicture",
                    data: formFile,
                    type: 'POST',
                    cache: false,
                    processData: false,
                    contentType: false,
                    success: function (result) {
                        // console.log(result)
                        $('button').show()
                        loading.style.display = 'none';
                        loading.innerText = '';
                        let reader = new FileReader()
                        reader.readAsDataURL(files[i]);
                        reader.onload = function (ev) {
                            let max = 720
                            let scale = 1
                            let canvas = document.createElement('canvas');
                            let context = canvas.getContext('2d');
                            canvas.style.display='block'
                            let image = new Image();
                            image.src = ev.target.result;
                            image.onload = function () {
                            // console.log(this)
                            if(this.width>max||this.height>max){
                                if(this.width > max){
                                scale = max / this.width;
                                }else{
                                    scale = max / this.height;
                                }
                            }
                            let cloud_count=0;
                            canvas.width=this.width*scale;
                            canvas.height=this.height*scale;
                            context.fillStyle = '#9fc5e8'
                            context.font = String(this.width*0.03*scale)+'px Georgia'

                            context.drawImage(image, 0, 0, this.width*scale, this.height*scale)
                            context.fillText('local count:'+detection.length, 10,35 )
                            for(let d=0;d<detection.length;d++){
                                console.log("det.length:"+detection.length)
                                console.log("count:"+result[d][1])
                                console.log(result[d][0])
                                context.strokeRect(detection[d]._box._x*scale, detection[d]._box._y*scale, detection[d]._box._width*scale, detection[d]._box._height*scale)
                                let canvas_point = result[d][0]
                                cloud_count+=result[d][1]
                                let point = canvas_point[0]
                                context.fillText(point['Name'], detection[d]._box._x*scale, detection[d]._box._y*scale)
                            }
                            context.fillText('cloud count:'+cloud_count, 10,55 )
                            // console.log(canvas)
                            $('#div-result').append(canvas)
                            }
                        }
                    }, //success
                }) //ajax
            } //onload
        }
    }
}