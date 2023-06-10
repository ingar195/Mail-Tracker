console.log("script.js loaded");

//function run the update function when the page loads
window.onload = function () {
	if (window.location.pathname === "/") {
		console.log("home page loaded");
		updateCarrierList();
		getParcels();
	}
	else if (window.location.pathname === "/config") {
		console.log("config page loaded");
		loadConfig();
	}
}

function loadConfig() {
	endpoint = "/api/config/get";
	data = apiCall(endpoint, { "config": "config" });

	// Set form values
	// document.getElementById("pbCheck").value = data.email;

}

function saveConfig() {
	// Get the form data
	const pbCheck = (document.getElementById('pbCheck')).checked;
	const pbApiKey = (document.getElementById('pbApiKey')).value;
	const pbAlerts = (document.getElementById('pbAlertsDropDown')).value;
	data = {
		"pushbullet": {
			"enabled": pbCheck,
			"token": pbApiKey,
			"alert_states": pbAlerts
		}
	}
	apiCall("/api/config/set", data)
}
function deletePackage(name) {
	// Get the form data
	console.log('Deleting package: ', name);
	endpoint = `/api/add_rm/rm/${name}`;
	apiCall(endpoint, {});
}

function handleKeyDown(event) {
	if (event.key === "Enter") {
		event.preventDefault(); // Prevent the default Enter key behavior (e.g., form submission)
		addPackage(); // Call the function to add a package
	}
}

function addPackage() {
	// Get the form data
	const trackingNumber = (document.getElementById('trackingNumber')).value;
	const carrier = (document.getElementById('carrierDropDown')).value;
	const parcelName = (document.getElementById('parcelName')).value;

	console.log('Adding package: ', parcelName, trackingNumber, carrier);
	endpoint = `/api/add_rm/add/${parcelName}`
	data = {
		carrier: carrier,
		tracking_number: trackingNumber
	}
	apiCall(endpoint, data)
}

function apiCall(endpoint, data) {
	fetch(endpoint, {
		method: "POST",
		headers: new Headers({ "content-type": "application/json" }),
		body: JSON.stringify(data)
	})
		.then(response => {
			if (response.ok) {
				console.log(response);
				return response.json(); // Return the promise from response.json()
			} else {
				throw new Error('Network response was not OK.');
			}
		})
		.then(data => {
			// Process the JSON data
			console.log('Data:', data);
			if (window.location.pathname === "/") {
				updatePackage(data);
			} else if (window.location.pathname === "/config") {
				for (const [name, packageData] of Object.entries(data)) {
					console.log(name, packageData);
					if (name === "pushbullet") {
						document.getElementById("pbCheck").checked = packageData.enabled;
						document.getElementById("pbApiKey").value = packageData.token;
						console.log("pbAlertsDropDown", packageData.alert_states);
					}
				}

			}


		})
		.catch (error => {
	// Handle any errors that occurred during the request or JSON parsing
	console.error('Error:', error);
});
}

function updatePackage(data) {
	console.log('Packages data:', data);
	const tableBody = document.getElementById('packagesTableBody');
	tableBody.replaceChildren();
	// Iterate over the packages data and generate table rows
	for (const [name, packageData] of Object.entries(data)) {
		const row = document.createElement('tr');

		const nameCell = document.createElement('td');
		nameCell.textContent = name;
		nameCell.classList.add('capitalize');
		row.appendChild(nameCell);

		const trackingNumberCell = document.createElement('td');
		trackingNumberCell.textContent = packageData.tracking_number;
		row.appendChild(trackingNumberCell);

		const carrierCell = document.createElement('td');
		carrierCell.textContent = packageData.carrier;
		carrierCell.classList.add('capitalize');
		row.appendChild(carrierCell);

		const etaCell = document.createElement('td');
		etaCell.textContent = packageData.eta;
		row.appendChild(etaCell);

		const shipmentStateCell = document.createElement('td');
		shipmentStateCell.textContent = packageData.shipment_state;
		shipmentStateCell.classList.add('capitalize');
		row.appendChild(shipmentStateCell);

		const locationStateCell = document.createElement('td');
		locationStateCell.textContent = packageData.location;
		locationStateCell.classList.add('capitalize');
		row.appendChild(locationStateCell);

		const actionCell = document.createElement('td');
		const button = document.createElement('button');
		button.textContent = 'Delete';
		button.id = name;
		button.onclick = function () {
			deletePackage(button.id);
		}
		actionCell.classList.add('button-cell');
		actionCell.appendChild(button);
		row.appendChild(actionCell);

		tableBody.appendChild(row);
	}
}

function getParcels() {
	console.log('Fetching packages...');
	fetch('/api/parcels/all')
		.then(response => response.json())
		.then(data => {
			updatePackage(data);
		});
}


function updateCarrierList() {
	// Get the selected value
	selected = document.getElementById("carrierDropDown").value
	// Get the new content
	fetch("/api/carrier")
		.then(response => response.json())
		.then(data => setSelectContent("carrierDropDown", data))
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