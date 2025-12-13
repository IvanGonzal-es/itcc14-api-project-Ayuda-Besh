// Philippines Regions and Cities Data
const philippinesRegions = {
    "Metro Manila (NCR)": [
        "Manila", "Quezon City", "Makati", "Taguig", "Pasig", "Mandaluyong",
        "San Juan", "Caloocan", "Las Piñas", "Parañaque", "Muntinlupa",
        "Marikina", "Valenzuela", "Malabon", "Navotas", "Pasay"
    ],
    "Ilocos Region (Region I)": [
        "Laoag", "Vigan", "San Fernando", "Alaminos", "Dagupan", "Urdaneta"
    ],
    "Cagayan Valley (Region II)": [
        "Tuguegarao", "Santiago", "Cauayan", "Ilagan"
    ],
    "Central Luzon (Region III)": [
        "Angeles", "Olongapo", "San Fernando", "Malolos", "Baliuag", "Cabanatuan",
        "Gapan", "Mabalacat", "Meycauayan", "San Jose del Monte", "Tarlac City"
    ],
    "CALABARZON (Region IV-A)": [
        "Antipolo", "Bacoor", "Cavite City", "Dasmariñas", "Imus", "Laguna",
        "Los Baños", "Lucena", "San Pablo", "Santa Rosa", "Tagaytay", "Tanauan",
        "Batangas City", "Calamba", "Lipa", "San Pedro"
    ],
    "MIMAROPA (Region IV-B)": [
        "Calapan", "Puerto Princesa", "Romblon", "Boac"
    ],
    "Bicol Region (Region V)": [
        "Legazpi", "Naga", "Iriga", "Sorsogon City", "Tabaco", "Ligao"
    ],
    "Western Visayas (Region VI)": [
        "Iloilo City", "Bacolod", "Roxas", "San Carlos", "Sipalay", "Cadiz"
    ],
    "Central Visayas (Region VII)": [
        "Cebu City", "Lapu-Lapu", "Mandaue", "Talisay", "Toledo", "Dumaguete",
        "Tagbilaran", "Bogo", "Carcar"
    ],
    "Eastern Visayas (Region VIII)": [
        "Tacloban", "Ormoc", "Calbayog", "Baybay", "Catbalogan", "Maasin"
    ],
    "Zamboanga Peninsula (Region IX)": [
        "Zamboanga City", "Dipolog", "Dapitan", "Pagadian", "Isabela"
    ],
    "Northern Mindanao (Region X)": [
        "Cagayan de Oro", "Iligan", "Oroquieta", "Ozamiz", "Tangub", "Gingoog"
    ],
    "Davao Region (Region XI)": [
        "Davao City", "Digos", "Mati", "Panabo", "Tagum"
    ],
    "SOCCSKSARGEN (Region XII)": [
        "General Santos", "Koronadal", "Cotabato City", "Kidapawan", "Tacurong"
    ],
    "Caraga (Region XIII)": [
        "Butuan", "Surigao City", "Tandag", "Bayugan", "Bislig"
    ],
    "Cordillera Administrative Region (CAR)": [
        "Baguio", "Tabuk", "La Trinidad", "Bontoc"
    ],
    "Bangsamoro Autonomous Region (BARMM)": [
        "Marawi", "Cotabato City", "Lamitan"
    ]
};

function populateLocationFilter(selectElement) {
    // Clear existing options except "All Locations"
    while (selectElement.options.length > 1) {
        selectElement.remove(1);
    }
    
    // Add regions and cities
    Object.keys(philippinesRegions).forEach(region => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = region;
        
        philippinesRegions[region].forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            optgroup.appendChild(option);
        });
        
        selectElement.appendChild(optgroup);
    });
}
