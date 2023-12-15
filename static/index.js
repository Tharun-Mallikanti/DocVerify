async function submitForm() {
    var formData = new FormData(document.getElementById('myForm'));
    var btn = document.getElementsByClassName("btn")[0];
    btn.disabled = true;
    const spinner = document.getElementById("spinner");
    spinner.classList.remove("d-none");
    const loadImageBase64 = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = (error) => reject(error);
        });
    }
    
    const fileInput = document.getElementById('fileInput');

    // Check if a file is selected
    if (fileInput.files.length > 0) {
        // Pass the selected file to loadImageBase64 function
        const image = await loadImageBase64(fileInput.files[0]);

        axios({
            method: "POST",
            url: "/submit",
            data: { image },
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then(function(response) {
            console.log(response.data)
            var resultImage = document.getElementById('resultImage');
            var list_class = document.getElementById('list_class');
            var bar = document.getElementById('bar');
            var bar_value = document.getElementById('bar_value');
            spinner.classList.add("d-none");
            list_class.classList.remove("d-none");
            bar.classList.remove("d-none");
            resultImage.src = 'data:image/jpeg;base64,'+response.data.roboflow_result;
            // details_arr=["emblem","goi","image","details","qr","aadharno"];
            let percentage=0;
            response.data.details_set.forEach(i => {
                console.log(i+percentage)
                if(i!="aadharlogo"){
                    percentage++;
                document.getElementById(i).src="/static/correct.gif";
                }
            });

            bar_value.style.width=(percentage/6)*100+'%'
            bar_value.innerHTML=(percentage/6)*100+'%'

            btn.disabled = false;
        })
        .catch(function(error) {
            console.error('Error:', error);
        });
    } else {
        console.error('No file selected');
    }
}
