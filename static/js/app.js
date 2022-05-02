window.onload = function () {
    var screenHeight = window.innerHeight
    var screenWidth = window.innerWidth
    var footer = document.getElementById('footer')
    var footer_distance_to_top = $("#footer").offset().top
    if (footer_distance_to_top > screenHeight) {
        footer.style.marginTop = "3vh"
        footer.style.marginBottom = "1.5vh"
    }
    else {
        var prev_siblings = footer.previousElementSibling
        var prev_siblings_height = prev_siblings.clientHeight
        var navi = document.getElementsByTagName('nav')
        var navi_height = navi[0].clientHeight
        var footer_height = footer.clientHeight
        console.log("screenHeight:" + screenHeight);
        console.log("screenWidth:" + screenWidth);
        console.log("prev_siblings_height" + prev_siblings_height);
        console.log("navi_height:" + navi_height);
        var footer_margin_top = screenHeight - prev_siblings_height - navi_height - footer_height - 0.05 * screenHeight
        footer.style.marginTop = footer_margin_top + "px"
        if (screenWidth < 760) {
            footer.style.fontSize = "3.5vw"
        }
    }
};