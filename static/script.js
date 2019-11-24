SOCKET_ADDR = 'http://localhost:5000/audio-sock';

socket = io.connect(SOCKET_ADDR);
mediaConstraint = {
	video: false,
	audio: {
		sampleRate: 44100,
		channelCount: 1
	}
};

navigator.getUserMedia = ( navigator.getUserMedia ||
                       navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia ||
                       navigator.msGetUserMedia);

function start_recording() {
	socket.emit("audio-start");
	$("#rec-btn")[0].innerText = "Starting...";
	$("#rec-btn").attr("onclick", "pass;");
}

function stop_recording() {
	audioRecorder.stop();
	socket.emit("audio-stop");

	$("#card-content")[0].innerHTML = "Waiting for results...";
}

socket.on("audio-started", function() {
	navigator.getUserMedia(mediaConstraint, function(stream) {
		audioRecorder = new MediaStreamRecorder(stream);
		audioRecorder.mimeType = 'audio/pcm';
		//audioRecorder.sampleRate = 22050;
		audioRecorder.audioChannels = 1;
		audioRecorder.ondataavailable = function(e) {
		    socket.emit("audio-tx", e);
		}
		audioRecorder.start(1000);
	}, function(error){

	});

	$("#rec-btn")[0].innerText = "Stop";
	$("#rec-btn").attr("onclick", "stop_recording();");
});

socket.on("trnsc-result", function(message) {
	$("#card-content")[0].innerHTML = message;
});

socket.on("interim-result", function(message) {
	$("#interim")[0].innerHTML = "<strong>Interim Results: </strong>" + message;
});
