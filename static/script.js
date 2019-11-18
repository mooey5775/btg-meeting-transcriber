SOCKET_ADDR = 'http://localhost:5000/audio-sock';

socket = io.connect(SOCKET_ADDR);
mediaConstraint = {
	video: false,
	audio: {
		sampleRate: 44100,
		channelCount: 1
	}
};

function start_recording() {
	socket.emit("audio-start");
	$("#rec-btn")[0].innerText = "Starting...";
	$("#rec-btn").attr("onclick", "pass;");
}

function stop_recording() {
	mediaRecorder.stop();
	socket.emit("audio-stop");

	$("#main-content")[0].innerHTML = "Waiting for results...";
}

socket.on("audio-started", function() {
	navigator.getUserMedia(mediaConstraint, function(stream) {
		mediaRecorder = new StereoAudioRecorder(stream);
		mediaRecorder.ondataavailable = function(e) {
		    socket.emit("audio-tx", e);
		}
		mediaRecorder.start(3000);
	}, function(error){

	});

	$("#rec-btn")[0].innerText = "Stop";
	$("#rec-btn").attr("onclick", "stop_recording();");
});

socket.on("trnsc-result", function(message) {
	$("#main-content")[0].innerHTML = message;
});
