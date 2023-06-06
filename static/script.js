console.log("script.js loaded")

//function run the update function when the page loads
window.onload = updateSelectList

// function to update the select list
function updateSelectList() {
    // Get the selected value
    selected = document.getElementById("packageList").value
    // Get the new content
    fetch("/api/parcels/" + "all")
        .then(response => response.json())
        .then(data => setSelectContent("packageList", data))
}


// Populate select list with stuff
function setSelectContent(selectID, content) {
    list = document.getElementById(selectID)
    list.replaceChildren()
    content.forEach((entry) => {
        list.appendChild(
            new Option(entry, entry)
        )
    })
}