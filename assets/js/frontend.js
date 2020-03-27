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

$("#startstop_button").on("click", function(){
	var action = $("#startstop_button").text();
	var list = "";
	var loop = $("#loop_checkbox").prop("checked");
	if (action == "Start"){
		$("#playlist").children("a").each(function(){
			list = list + $(this).text() + ";";
		});
		if (list != "")
		{
			$("#startstop_button").text("Stop");
			$.post("/start", {newplaylist: list, loop: loop}, function(data, result){
				poll();
			});
		}
	}
	else {
		$("#startstop_button").text("Start");
		$("#startstop_button").prop( "disabled", true );
		$.post("/stop", function(data, result){
			poll();
		});
	}
});

function poll() {
	$.ajax({ url: "/status", success: function(data){
			if (data.status == "stopped"){
				$("#startstop_button").prop( "disabled", false );
			}
			var command = data.status == "running" ? "Stop" : "Start";
			$("#startstop_button").text(command);
		}, dataType: "json" })

		.done(function(data){
			if (data.status != "stopped"){
				setTimeout(function() {
					poll();
				}, 3000);
			}
		});
};

$( document ).ready(function() {
		poll();
});

$("#file_upload").change(function(){
		//alert("new file: " + this.files[0].name);
		var form = document.getElementById("file_uploader_form");
		form.submit();
});

$(function(){
	$("#add_ledsection").on("click", function(e){
				var container = $("#ledsection_container");
				var sections = container.children("div");
				var newNr = sections.length + 1;
				var newDiv = sections.last().clone();
				newDiv.appendTo(container);
				var label = newDiv.find("label").first();
				label.text("LED Color " + newNr + ":");
				var input = newDiv.find("input").first();
				input.attr("name", "led_color" + newNr);
		});
});