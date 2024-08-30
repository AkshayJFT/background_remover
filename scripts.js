document.getElementById('fileInput').addEventListener('change', function(event) {
    const reader = new FileReader();
    reader.onload = function() {
        const image = document.getElementById('uploadedImage');
        image.src = reader.result;
        image.style.display = 'block';
        document.getElementById('imageText').style.display = 'none';
    };
    reader.readAsDataURL(event.target.files[0]);
});

document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const formData = new FormData();
    const fileField = document.querySelector('input[type="file"]');
    formData.append('file', fileField.files[0]);

    const response = await fetch('http://127.0.0.1:8000/segment-image/', {
        method: 'POST',
        body: formData,
    });

    if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const processedImage = document.getElementById('processedImage');
        processedImage.src = url;
        processedImage.style.display = 'block';
        document.getElementById('processedImageText').style.display = 'none';

        const downloadButton = document.getElementById('downloadButton');
        downloadButton.href = url;
        document.getElementById('downloadSection').style.display = 'block';
    } else {
        alert('There was an error processing your image. Please try again.');
    }
});
