$(function(){
  $("#playlist").on("click", "a", function(e){
    e.preventDefault(); //stops the link from doing it's normal thing
    e.target.parentNode.removeChild(e.target);  
  });
});

$(function(){
  $("#tracks_list").on("click", "a", function(e){
    e.preventDefault(); //stops the link from doing it's normal thing
    document.getElementById("playlist").appendChild(e.target.cloneNode(true));  
  });
});

$("#start_button").on("click", function(){
  var list = "";
  var loop = document.getElementById("loop_checkbox").checked;
  $("#playlist").children("a").each(function(){
    list = list + $(this).text() + ";";
  });
  $.post("/start", {newplaylist: list, loop: loop}, function(data, result){
    //alert("data: " + data + ", result: " + result);
  });
});

$("#stop_button").on("click", function(){
  $.post("/stop", function(data, result){
    //alert("data: " + data + ", result: " + result);
  });
});

$("#file_upload").change(function(){
    //alert("new file: " + this.files[0].name);
    var form = document.getElementById("file_uploader_form");
    form.submit();
});