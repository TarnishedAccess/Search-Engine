const searchButtonText = document.getElementById('searchButtonText');
const inputField = document.getElementById('searchInputText');

function treatSearchInput(searchInput) {
    // Splits the search input by space and +
    let searchInputSplitOr = searchInput.split('+');
    searchInputSplitOr = searchInputSplitOr.map((item) => item.trim())
    let searchInputSplitSpace = searchInputSplitOr.map((item) => item.split(' '));
    searchInputSplitSpace = searchInputSplitSpace.join('|');
    return searchInputSplitSpace
}

async function getImageText(keywords) {
    try {
        const response = await fetch(`http://127.0.0.1:8080/images_by_keywords?keywords=${keywords}`, {
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
        console.error('Error fetching images:', error);
        throw error;
    }
}

function displayImages(data) {
    const images = data.images;
    const imageContainer = document.getElementById('imageContainer');
    imageContainer.innerHTML = '';
  
    let row = document.createElement('div');
    row.classList.add('imageRow');
  
    images.forEach((image, index) => {
      const img = document.createElement('img');
      img.src = "images/" + image;
      img.classList.add('foundImages');
      img.style.width = '250px';
      img.style.height = '250px';
  
      row.appendChild(img);
  
      if ((index + 1) % 4 === 0 || index === images.length - 1) {
        if (index === images.length - 1 && images.length % 4 !== 0) {
          const remaining = 4 - (images.length % 4);
          for (let i = 0; i < remaining; i++) {
            const fakeImg = document.createElement('div');
            fakeImg.style.width = '250px';
            fakeImg.style.height = '250px';
            fakeImg.style.background = 'transparent';
            fakeImg.classList.add('fakeImages');
            row.appendChild(fakeImg);
          }
        }
        imageContainer.appendChild(row);
        row = document.createElement('div');
        row.classList.add('imageRow');
      }
    });
  }

searchButtonText.addEventListener('click', () => {
    const keyword = inputField.value;
    const result = treatSearchInput(keyword)
    getImageText(result)
    .then(data => {
        displayImages(data);
    })
});