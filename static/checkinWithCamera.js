try{
    $('#end-checkin-btn').hide()
    var mediaStreamTrack = null;
    var send_flag = 'OFF';
    var unknown_count = 0;
    var step = 0;

} catch (e) {
    send_flag = 'OFF';
    mediaStreamTrack = null;
    unknown_count = 0;
    step = 0;
}

$('.stu_info_box').mousedown(function () {
    let canMove;
    let last_x;
    let last_y;
    canMove = true;
    $('.stu_info_box').mousemove(function (e) {
        if(canMove === true) {
            // console.log(last_x)
            let offset = $('.stu_info_box').offset();
            // console.log(offset)
            if(last_x!==undefined){
                let x = e.pageX - last_x;
                let y = e.pageY - last_y;
                $(this).css({'left':offset.left+x,'top':offset.top+y})
                if(offset.left+x<100){
                    $(this).css({'left':101})
                }
                if(offset.top+y<50){
                    $(this).css({'top':51})
                }
                if(offset.top+y>500){
                    $(this).css({'top':499})
                }
                if(offset.left+x>2000){
                    $(this).css({'top':1999})
                }
            }
            // console.log(offset.left)

            last_x=e.pageX;
            last_y=e.pageY;
        }
    })
    $('.stu_info_box').mouseup(function () {
    canMove = false;
})
})



// function searchImage(image1, image2, tmplw, tmplh) {
//     if(image2===0){
//         return 0;
//     }
//     // var canvas = document.createElement('canvas'),
//     // ctx = canvas.getContext('2d'),
//     // sw = image1.width,  // 原图宽度
//     // sh = image1.height,  // 原图高度
//     // tw = tmplw || 8,  // 模板宽度
//     // th = tmplh || 8;  // 模板高度
//     // canvas.width = tw;
//     // canvas.height = th;
//     // ctx.drawImage(image1, 0, 0, sw, sh, 0, 0, tw, th);
//     let ctx = image1.getContext('2d')
//     let pixels = ctx.getImageData(0, 0, 480, 360);
//     pixels = toGrayBinary(pixels, true, null, true);
//     // let canvas2 = document.createElement('canvas');
//     // let ctx2 = canvas2.getContext('2d');
//     // canvas2.width = tw;
//     // canvas2.height = th;
//     // ctx2.drawImage(image2, 0, 0, image2.width, image2.height, 0, 0, tw, th);
//     let ctx2 = image2.getContext('2d')
//     let pixels2 = ctx2.getImageData(0, 0, 480, 360);
//     pixels2 = toGrayBinary(pixels2, true, null, true);
//     let similar = 0;
//     for (let i = 0, len = 480 * 360; i < len; i++) {
//         if (pixels[i] == pixels2[i]) similar++;
//     }
//     similar = (similar / (480 * 360)) * 100;
//     return similar;
// }
// // 像素数据，是否二值化（bool），二值化闵值（0-255），是否返回二值化后序列（bool）
// function toGrayBinary(pixels, binary, value, sn) {
//     var r, g, b, g, avg = 0, len = pixels.data.length, s = '';
//     for (var i = 0; i < len; i += 4) {
//         avg += (.299 * pixels.data[i] + .587 * pixels.data[i + 1] + .114 * pixels.data[i + 2]);
//     }
//     avg /= (len / 4);
//     for (var i = 0; i < len; i += 4) {
//         r = .299 * pixels.data[i],
//         g = .587 * pixels.data[i + 1],
//         b = .114 * pixels.data[i + 2];
//         if (binary) {
//             if ((r + g + b) >= (value || avg)) {
//                 g = 255;
//                 if (sn) s += '1';
//             } else {
//                 g = 0;
//                 if (sn) s += '0';
//             }
//             g = (r + g + b) > (value || avg) ? 255 : 0;
//         } else {
//             g = r + g + b;
//         }
//         pixels.data[i] = g,
//         pixels.data[i + 1] = g,
//         pixels.data[i + 2] = g;
//     }
//     if (sn) return s;
//     else return pixels;
// }

async function pre_process(last_trace) {
    let camera = document.getElementById('camera')
    let canvas_draw = document.getElementById('canvas_draw')
    let ctx_draw = canvas_draw.getContext('2d')
    let canvas_crop = document.getElementById('canvas_crop')
    let ctx_crop = canvas_crop.getContext('2d')
    let canvas_combined = document.getElementById('canvas_combined')
    let ctx_combined = canvas_combined.getContext('2d')

    // canvas_crop.width=160
    // canvas_crop.height=160
    // canvas_combined.height=160
    
    // canvas_crop.width=480
    // canvas_crop.height=360
    ctx_draw.drawImage(camera,0,0,480,360)
    // console.log(step)
    if(step%10 !== 0){
        setTimeout(function () {
            if(send_flag==='OFF'){clearTimeout(this)}else {
                pre_process(last_trace)
            }
        },10)
        step++;
        return;
    }
    step = 1;


    let detection = await faceapi.detectAllFaces(canvas_draw)
    if(detection.length===0){
        // let this_trace = []
        setTimeout(function () {
            if(send_flag==='OFF'){clearTimeout(this)}else {
                pre_process(last_trace)
            }
        },10)

    }else{
        
        // canvas_combined.width=0

        let dist_tolerate = 5
        let scale = 0
        let trace = []
        // console.log(last_prediction)
        
        for(let i=0;i<detection.length;i++){
            if(detection[i]._score<0.75){
                continue;
            }

            if(last_trace.length===0){
                let this_trace = {x:detection[i]._box._x,y:detection[i]._box._y,dx:0,dy:0,lasting:0}
                // let this_trace = {x:0,y:0,dx:0,dy:0}
                trace.push(this_trace)
                continue;
            }
            
            let found = false

            let tmp = 0;
            
            for(let j=0;j<last_trace.length;j++){
                let dx = detection[i]._box._x-last_trace[j].x
                let dy = detection[i]._box._y-last_trace[j].y
                if(dx > 50 || dy > 50){
                    tmp++;
                    continue;
                }
                // console.log(Math.abs(dx-last_trace[j].dx),Math.abs(dy-last_trace[j].dy))
                if(Math.abs(dx-last_trace[j].dx)<dist_tolerate && Math.abs(dy-last_trace[j].dy)<dist_tolerate || (dx<dist_tolerate && dy<dist_tolerate)){
                    let this_trace = {x:detection[i]._box._x,y:detection[i]._box._y,dx:dx,dy:dy,lasting:last_trace[j].lasting+1}
                    if(this_trace.lasting>=7){
                        ctx_draw.strokeStyle="#00ff1a"
                        ctx_draw.strokeRect(detection[i]._box._x,detection[i]._box._y,detection[i]._box._width,detection[i]._box._height)
                        ctx_crop.drawImage(canvas_draw,detection[i]._box._x-scale,detection[i]._box._y-scale,detection[i]._box._width+scale*2,detection[i]._box._height+scale*2,0,0,canvas_crop.width,canvas_crop.height)
                        ctx_combined.drawImage(canvas_crop,canvas_combined.width-155,0)
                        resize_canvas(canvas_combined,canvas_combined.width+160,160)
                        this_trace.lasting = 0;
                        found = true;
                        break;
                    }else {
                        trace.push(this_trace)
                        found = true
                        ctx_draw.strokeStyle="#fffd00";
                        ctx_draw.strokeRect(detection[i]._box._x,detection[i]._box._y,detection[i]._box._width,detection[i]._box._height)
                        break;
                    }
                }
            }
            if(found===false){
                let this_trace = {x:detection[i]._box._x,y:detection[i]._box._y,dx:0,dy:0,lasting:1}
                trace.push(this_trace)
                break;
            }
        }
        if(canvas_combined.width>170){
            sendImage(canvas_combined);
            canvas_combined.width = 160;
        }

        setTimeout(function () {
                        if(send_flag==='OFF'){clearTimeout(this)}else {
                            pre_process(trace)
                        }
                    },10)

    }
}

function sendImage(canvas_combined) {
        if(send_flag==='OFF'){
            return;
        }
        let image = canvas_combined.toDataURL('image/jpeg',0.9);
            $.ajax({
            url:'/CheckInWithCamera',
            type:'POST',
            data:image,
            beforeSend:function (xhr) {
                xhr.setRequestHeader("Content-type", "image/jpeg")
            },
            success:function (res) {
                let jsonR = jsonifyRes(res)
                let data;
                if (jsonR.code === 3000) {
                    data = jsonR.data
                    // console.log(data)
                    if (data.length === 0) {
                        return -1;
                    } else {
                        // console.log(data)
                        // ctx_draw.drawImage(canvas_prototype, 0, 0)
                        for (let i = 0; i < data.length; i++) {
                            let canvas_point = data[i]
                            // ctx_draw.strokeRect(Number(canvas_point['canvas_x']), Number(canvas_point['canvas_y']), Number(canvas_point['canvas_width']), Number(canvas_point['canvas_height']))
                            // ctx_draw.fillStyle = '#9fc5e8'
                            // ctx_draw.font = '30px Georgia'
                            // ctx_draw.fillText(canvas_point['canvas_text'], Number(canvas_point['canvas_x']), Number(canvas_point['canvas_y']))
                            if(canvas_point['CID']==='unknown'){
                                unknown_count++;
                                document.getElementById('unknown_count').innerText=String(unknown_count)
                            }else {
                                try{
                                    document.getElementById(canvas_point['CID']).innerText='Checked'
                                }catch  {
                                    console.log('OUT ACCESS')
                                }
                            }
                        }
                        // setTimeout(function () {
                        //     if(send_flag==='OFF'){clearTimeout(this)}else {
                        //         pre_process(detection,prediction)
                        //     }
                        // },10)
                    }
                } else {
                    handleCode(jsonR)
                }
            }
        })
    }
async function startCheckin() {
    $('.video_box').show()
    $('button').hide()
    $(".loading_models").innerText='loading'
    await faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models')
    $('.loading_models').innerText=''
    $('#end-checkin-btn').show()

    send_flag = 'ON'

    let constraints = {
        video:true
    };
    // get video camera
    let video = document.getElementById('camera');
    let video_promise = navigator.mediaDevices.getUserMedia(constraints);
    video_promise.then((mediaStream)=>{
        mediaStreamTrack = typeof mediaStream.stop === 'function' ? mediaStream : mediaStream.getTracks()[0]
        video.srcObject = mediaStream;
        video.play()
    });
    $.ajax({
        url:'/getStuList',
        type:'GET',
        success:function (res) {
            stu_box = document.getElementsByClassName('.stu_info_box')
            for (let i = 0; i < res.length; i++) {
                let new_div = document.createElement('div')
                new_div.className = 'stu_info_line'
                // $(".stu_info_line")
                new_div.innerHTML = "<span>" + res[i].CID + "</span><span>" + res[i].NAME + "</span><span id="+res[i].CID+"></span>"
                $('.stu_info_box').append(new_div)
            }
        }
    })
    let prediction = []
    await pre_process(prediction,0)
}
function endCheckin() {
    unknown_count = 0
    $('.video_box').hide()
    setTimeout(function () {
        $('.stu_info_line').remove()
    },1000)
    send_flag = 'OFF';
    $('button').show()
    $('#end-checkin-btn').hide()
    mediaStreamTrack && mediaStreamTrack.stop()
    // $('#canvas_draw').style.display='none'
    setTimeout(function () {
        $.ajax({
        url: '/endCheckin',
        type: 'GET',
        beforeSend:function (xhr) {
            xhr.setRequestHeader('token',localStorage.token)
        },
        success:function (res) {
            let jsonR = jsonifyRes(res)
            if(jsonR.code===3001){
                window.location.href='/downloadfile?filepath='+jsonR.path
            }else {
                handleCode(jsonR)
            }
        }
    })
    },2000)
}