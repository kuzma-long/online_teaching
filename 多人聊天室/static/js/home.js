var id = $("#id").val()
var user = $("#user").val()
var name = $("#name").val()

host = "ws://127.0.0.1:8000/newClient?id=" + id + "&name=" + name + "&user=" + user
websocket = new WebSocket(host)
websocket.onopen = function (evt) {
}      // 建立连接
websocket.onmessage = function (evt) {    // 获取服务器返回的信息
    data = $.parseJSON(evt.data)        // 将获得的消息添加到聊天框
    if (data['from'] == 'system') {
        $('#chatinfo').append("<div class='systime'><b>" + data['time'] + "</b></div>");
        $('#chatinfo').append("<p class='sysmsg'>" + data['message'] + "</p>");
        words = data['message'].split(' ')
        if (words[1] == "加入聊天室") {
            var obj = document.getElementById("atusers")
            obj.options.add(new Option(words[0], words[0]));
        } else if (words[1] == "离开聊天室") {
            var obj = document.getElementById("atusers")
            var index = 0
            for (var i = 0; i < obj.options.length; i++) {
                if (obj.options[i].value == words[0])
                    index = i
            }
            obj.options.remove(index)
        }
    } else if (data['from'] == user) {
        $('#chatinfo').append("<div class='usr'><b>" + data['time'] + "</b><div id='usrfrom'>" + user + "</div><div id='usrmsg'>" + data['message'] + "</div></div>");
    } else {
        $('#chatinfo').append("<div class='other'><b>" + data['time'] + "</b><div id='otherfrom'>" + user + "</div><div id='othermsg'>" + data['message'] + "</div></div>");
    }
}
websocket.onerror = function (evt) {
}

function send() {    // 向服务器发送信息
    var message = $("#chat_text").val()
    if ($("#atusers").val() != null) {
        message += ' @'
        message += $("#atusers").val()
    }
    websocket.send(message)
    $("#chat_text").val("")
    var obj = document.getElementById("atusers")
    obj.selectedIndex = -1
}