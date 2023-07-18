$(function () {
    $("#playlist").on("click", "a", function (e) {
        e.preventDefault();
        e.target.parentNode.removeChild(e.target);
    });
});

$(function () {
    $("#tracks_list").on("click", "a", function (e) {
        e.preventDefault();
        document.getElementById("playlist").appendChild(e.target.cloneNode(true));
    });
});

const startStopButton = $("#startstop_button");
startStopButton.on("click", function () {
    const action = startStopButton.text();
    let list = "";
    const loop = $("#loop_checkbox").prop("checked");
    if (action === "Start") {
        $("#playlist").children("a").each(function () {
            list = list + $(this).text() + ";";
        });
        if (list !== "") {
            startStopButton.text("Stop");
            $.post("/start", {newplaylist: list, loop: loop}, function (data) {
                feedback(data.message);
                poll();
            });
        }
    } else {
        startStopButton.text("Start");
        startStopButton.prop("disabled", true);
        $.post("/stop", function (data) {
            feedback(data.message);
        });
    }
});

function poll(silent= false) {
    $.ajax({
        url: "/status", success: function (data) {
            if (data.status === "stopped") {
                startStopButton.prop("disabled", false);
                if (!silent) {
                    feedback("Playlist stopped");
                }
            }
            const command = data.status === "running" ? "Stop" : "Start";
            startStopButton.text(command);
        }, dataType: "json"
    }).done(function (data) {
        if (data.status !== "stopped") {
            setTimeout(function () {
                poll();
            }, 3000);
        }
    });
}

$(document).ready(function () {
    poll(true);
});

$("#file_upload").change(function () {
    const form = $('#file_uploader_form');
    const actionUrl = form.attr('action');
    const data = new FormData($("#file_uploader_form")[0]);

    $.ajax({
        type: "POST",
        url: actionUrl,
        data: data,
        processData: false,
        contentType: false
    }).always(function (data) {
        feedback(data.message);
    });
});

$(function () {
    $("#add_ledsection").on("click", function () {
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

$(function () {
    $("#remove_ledsection").on("click", function () {
        const container = $("#ledsection_container");
        const sections = container.children("div");
        if (sections.length > 1) {
            sections.last().remove();
        }
    });
});

$("#light_button").on("click", function () {
    let list = "";
    $("#ledsection_container").find("input").each(function () {
        list = list + $(this).val() + ";";
    });
    if (list !== "") {
        $.post("/lighting", {newcolors: list}, function (data) {
            feedback(data.message);
        });
    }
});

function feedback(message) {
    toastr.options.positionClass = 'toast-bottom-right'
    toastr.info(message);
}

function shutdown() {
    $.post("shutdown", {}, function (data) {
        feedback(data.message);
    });
}

function exit() {
    $.post("exit", {}, function (data) {
        feedback(data.message);
    });
}
