document.addEventListener("DOMContentLoaded", function () {
  var dropzone = document.getElementById("dropzone");
  var input = document.getElementById("mushroom_image");
  var fileName = document.getElementById("file-name");
  var previewWrap = document.getElementById("preview-wrap");
  if (!dropzone || !input) return;

  function showPreview(file) {
    if (!file) return;
    fileName.textContent = file.name;
    var reader = new FileReader();
    reader.onload = function (e) {
      previewWrap.innerHTML = '<img src="' + e.target.result + '" alt="preview">';
    };
    reader.readAsDataURL(file);
  }

  input.addEventListener("change", function () {
    showPreview(input.files[0]);
  });

  ["dragenter", "dragover"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });
  ["dragleave", "drop"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });
  dropzone.addEventListener("drop", function (e) {
    var files = e.dataTransfer.files;
    if (files && files.length) {
      input.files = files;
      showPreview(files[0]);
    }
  });
});
