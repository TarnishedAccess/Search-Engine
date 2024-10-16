const searchButtonText = document.getElementById('searchButton');
const inputField = document.getElementById('searchInputText');

async function getImageText(keyword) {
    try {
        const response = await fetch(`http://127.0.0.1:8080/images_by_keyword?keyword=${keyword}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('Error fetching connected drones:', error);
        throw error;
    }
}

function displayImages(data) {
    images = data.images
    const imageContainer = document.getElementById('imageContainer');
    imageContainer.innerHTML = '';
    images.forEach(image => {
        const img = document.createElement('img');
        img.src = "images/" + image;
        imageContainer.appendChild(img);
    });
}

searchButtonText.addEventListener('click', () => {
    const keyword = inputField.value;
    getImageText(keyword)
    .then(data => {
        displayImages(data);
    })
});