$("div").submit(function (evt) {
    var pwd1 = $("#password1").val()
    var pwd2 = $("#password2").val()
    if (pwd1 != pwd2) {
        evt.preventDefault()
        alert("密码确认不一致！")
    }
})