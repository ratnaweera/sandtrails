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

const startStopButton = $("#startstop_button");
startStopButton.on("click", function(){
	const action = startStopButton.text();
	let list = "";
	const loop = $("#loop_checkbox").prop("checked");
	if (action === "Start"){
		$("#playlist").children("a").each(function(){
			list = list + $(this).text() + ";";
		});
		if (list !== "")
		{
			startStopButton.text("Stop");
			$.post("/start", {newplaylist: list, loop: loop}, function(){
				poll();
			});
		}
	}
	else {
		startStopButton.text("Start");
		startStopButton.prop( "disabled", true );
		$.post("/stop", function(){
			poll();
		});
	}
});

function poll() {
	$.ajax({ url: "/status", success: function(data){
		if (data.status === "stopped"){
			startStopButton.prop( "disabled", false );
		}
		const command = data.status === "running" ? "Stop" : "Start";
		startStopButton.text(command);
	}, dataType: "json" })

	.done(function(data){
		if (data.status !== "stopped"){
			setTimeout(function() {
				poll();
			}, 3000);
		}
	});
}

$( document ).ready(function() {
	poll();
});

$("#file_upload").change(function(){
	const form = document.getElementById("file_uploader_form");
	form.submit();
});

$(function(){
	$("#add_ledsection").on("click", function(){
		const container = $("#ledsection_container");
		const sections = container.children("div");
		const newNr = sections.length + 1;
		const newDiv = sections.last().clone();
		const label = newDiv.find("label").first();
		label.prop("id", "colorpicker_label" + newNr);
		label.prop("for", "colorpicker" + newNr);
		label.text("LED Color " + newNr + ":");
		const input = newDiv.find("input").first();
		input.prop("id", "colorpicker" + newNr);
		input.attr("name", "led_color" + newNr);
		newDiv.appendTo(container);
	});
});

$(function(){
	$("#remove_ledsection").on("click", function(){
		const container = $("#ledsection_container");
		const sections = container.children("div");
		if (sections.length > 1) {
			sections.last().remove();
		}
	});
});

$("#light_button").on("click", function(){
	let list = "";
	$("#ledsection_container").find("input").each(function(){
		list = list + $(this).val() + ";";
	});
	if (list !== "")
	{
		$.post("/lighting", {newcolors: list}, function(data, result){
		});
	}
});
