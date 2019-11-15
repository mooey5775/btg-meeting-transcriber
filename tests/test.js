var socket = io.connect('http://localhost:5000/test');
var mediaConstraint = { video: false, audio: true };
navigator.getUserMedia(mediaConstraint, function(stream) {
    var mediaRecorder = new StereoAudioRecorder(stream);
    mediaRecorder.ondataavailable = function(e) {
        socket.emit("audio-tx", e);
    }
	mediaRecorder.start(3000);
}, function(error){

});
