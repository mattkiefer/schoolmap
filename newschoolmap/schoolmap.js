/* config start */
prod = false;
prod_data_url = "https://s3.amazonaws.com/projects.chicagoreporter.com/graphics/newschoolmap/test2.geojson";
test_data_url = "geo_schools.geojson";
mapboxgl.accessToken = 'pk.eyJ1IjoibWF0dGhld2xraWVmZXIiLCJhIjoiY2l4MGxscGY5MDFkMDJ0bzBvZTE5Ym1wMyJ9.iBxJV6lSLtj4iRf7n-VQDg';
var mbStyleURL = 'mapbox://styles/matthewlkiefer/ciy1vzzn600792rqj7de09u8q' // </3
var mapCenter = [-87.55, 41.8195]
var mapZoom = 9.5
var mapMinZoom = 9.5
var mapMaxZoom = 15
/* config end */


if (prod) {
    data_url = prod_data_url;
} else {
    data_url = test_data_url;
}


// global var for map, table data
jdata = null;
listen = false;


/* get data, then makeMap() */
$.ajax({
    url: data_url,
    dataType: "jsonp",
    jsonpCallback: 'callback',
    success: function(response) { jdata = response; makeMap(response)}
});

/* making map */
    var mbmap = new mapboxgl.Map({
        container: 'map',
        style: mbStyleURL,
        center: mapCenter,
        zoom: mapZoom,
        minZoom: mapMinZoom,
        maxZoom: mapMaxZoom,
    });


makeMap = function(jdata) {
    mbmap.addControl(new mapboxgl.NavigationControl());

    mbmap.on('click', function (e) {
            var features = mbmap.queryRenderedFeatures(e.point,{layers:['sold','for sale','repurposed']})
                if (features.length) {  
                    render_properties(features[0].properties);
            }
        }
    )


    mbmap.on('load', function(e) {
        mbmap.addSource('places', {
            type: 'geojson',
            data: jdata, 
        });
        jdata.features.forEach(function(school) {
            var school_status = school.properties['status'];
            var symbol = status_icons[school_status];
            var layerID = school_status;
            if (!mbmap.getLayer(layerID)) {
                layer = mbmap.addLayer({
                    "id": layerID,
                    "type": 'symbol',
                    "source": 'places',
                    "layout": {
                        'icon-image': symbol,
                        'icon-allow-overlap': true
                    },
                    "filter": ["==", "status", school_status]
                })
            }
        });
    });
    makeTable(jdata.features);
    listen = true;
    hashHandler();
};


makeTable = function(schools) {
    table_data = buildArray(schools);
    $(document).ready( function () {
        $('#schools-table').DataTable({
            data:table_data,
            columns: [
                    {title:"school"},
                    {title:"address"},
                    {title:"community area"},
                    {title:"status"},
            ],
            bPaginate: false,
            bInfo: false,
        });
    });
};


buildArray = function(schools) {
    data = [];
    for (i in schools) {
        row = []
        school = schools[i].properties;
        row.push(school.link,school.address,school.comm_area,school.status)
        data.push(row)
    };
    return data;
}


hashHandler = function() {
    debugger;
    hash = document.location.hash.replace("#","");
    if (hash.length && listen) {
        school = lookupSchool(hash);   
//        goToTop(hash);
        zoomCenterInfo(school);
    }
}


lookupSchool = function(hash) {
    return jdata.features.find(s=>s.properties.slug==hash);
}


zoomCenterInfo = function(school){
    render_properties(school.properties);
    lat = +(school.geometry.coordinates[1])
    lon = +(school.geometry.coordinates[0])
    mbmap.flyTo({
        center: [lon,lat],
        zoom: mapMaxZoom,
        speed: 1,
    });
}


window.addEventListener("hashchange",hashHandler,false);


render_properties = function(properties) {
    //glide to map
    $('html, body').animate({
        scrollTop: $("#map-anchor").offset().top
    }, 1000);
    // infobox should include ul of data
    // and also ul of legend elements
    // ... so just empty() the data
    infobox = $('#infobox');
    $('#legend').before($("<ul>").attr("id","school-listing"));
    schoolListing = $("#school-listing")
    schoolListing.empty();
    
    // well! coulda done this neater ...
    $("<li>").attr("id","school-name").appendTo(schoolListing);
    $("#school-name")[0].innerText = properties['name'];
    
    $("<li>").attr("id","school-address").appendTo(schoolListing);
    $("#school-address")[0].innerText = properties['address'];
    
    $("<li>").attr("id","school-commarea").appendTo(schoolListing);
    $("#school-commarea")[0].innerText = properties['comm_area'];
    
    $("<li>").attr("id","school-status").appendTo(schoolListing);
    $("#school-status")[0].innerText = properties['status'];
    
    $("<li>").attr("id","school-usage").appendTo(schoolListing);
    $("#school-usage")[0].innerText = properties['usage'];

    $("<li>").attr("id","school-saledoc").appendTo(schoolListing);
    $("#school-saledoc")[0].innerText = properties['sale_doc'];

    $("<li>").attr("id","school-repurposedoc").appendTo(schoolListing);
    $("#school-repurposedoc")[0].innerText = properties['repurpose_doc'];
    
    $("<li>").attr("id","school-alderman").appendTo(schoolListing);
    $("#school-alderman")[0].innerText = properties['alderman'];
    
    $("<li>").attr("id","school-saledate").appendTo(schoolListing);
    $("#school-saledate")[0].innerText = properties['sale_date'];
    
    $("<li>").attr("id","school-buyer").appendTo(schoolListing);
    $("#school-buyer")[0].innerText = properties['buyer'];
   
    $("<li>").attr("id","school-price").appendTo(schoolListing);
    $("#school-price")[0].innerText = properties['price'];

    console.log(properties)
}


status_icons = {
    'sold': 'sold_school-15',
    'for sale': 'unsold_school-15',
    'repurposed': 'repurposed_school-15'
};

