/* config start */
prod = true;
prod_data_url = "https://s3.amazonaws.com/projects.chicagoreporter.com/graphics/newschoolmap/geo_schools.geojson";
test_data_url = "geo_schools.geojson";
mapboxgl.accessToken = 'pk.eyJ1IjoibWF0dGhld2xraWVmZXIiLCJhIjoiY2l4MGxscGY5MDFkMDJ0bzBvZTE5Ym1wMyJ9.iBxJV6lSLtj4iRf7n-VQDg';
var mbStyleURL = 'mapbox://styles/matthewlkiefer/ciy1vzzn600792rqj7de09u8q' // </3
var mapCenter = [-87.63, 41.8195]
var mapZoom = 10
var mapMinZoom = 10
var mapMaxZoom = 16
var mapReady = false;
var tableReady = false;
/* config end */


// test or prod
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
                    // TODO: abstract this
                    school = features[0]
                    window.location.hash = school.properties.slug;
                    render_properties(school.properties);
                    zoomCenterInfo(school);
            }
        }
    )
    mbmap.on('load', function(e) {
        mbmap.addSource('places', {
            type: 'geojson',
            data: jdata, 
        });
        mbmap.addControl(new mapboxgl.NavigationControl());
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
    glideToMap();
    hashHandler();
    displayInstructions();
    });
    makeTable(jdata.features);
    listen = true;
    mapReady = true;
    checkReady();
};

displayInstructions = function() {
    if (!window.location.hash.length) {
        infobox = $('#infobox')[0];
        $('#legend').before($("<p>").attr("id","instructions")); 
        $('#instructions')[0].innerHTML = 'Select a school by location or <a href="#table-anchor">name</a>.';    
    }
}

makeTable = function(schools) {
    table_data = buildArray(schools);
    $(document).ready( function () {
        $('#schools-table').DataTable({
            data:table_data,
            columns: [
                    {title:"School"},
                    {title:"Address"},
                    {title:"Community area"},
                    {title:"Status"},
            ],
            bPaginate: false,
            bInfo: false,
            bAutoWidth: true,
            initComplete: function(){tableReady=true;checkReady();},
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

// force things to fit in wordpress post
crowBar = function(){
    $(".entry-content").height(
        $("#map").height() + $("#schools-table").height() + $("#chatter").height() + 400
    );
}

checkReady = function(){
    if (mapReady && tableReady) {
        crowBar();
    }
}

hashHandler = function() {
    hash = document.location.hash.replace("#","");
    if (hash=='map-anchor'){return}
    if (hash.length && listen) {
        school = lookupSchool(hash);   
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


glideToMap = function(){
    $('html, body').animate({
        scrollTop: $("#map").offset().top - 100
    }, 1000);
}


resetMapInfo = function(){
    $("#xout").remove();
    window.location.hash = ''
    if ($("#school-listing")){$("#school-listing").remove();};
    displayInstructions() 
    mbmap.flyTo({
        center: mapCenter,
        zoom: mapZoom,
        speed: 1,
    })
}


render_properties = function(properties) {
    glideToMap();
    // infobox should include ul of data
    // and also ul of legend elements
    // ... so just empty() the data
    infobox = $('#infobox');
    if ($("#instructions")){$("#instructions").remove();};
    $('#legend').before($("<ul>").attr("id","school-listing"));
    schoolListing = $("#school-listing")
    schoolListing.empty();

    if ($("#xout")){$("#xout").remove();};
    $("#school-listing").before($("<h1>").attr("id","xout"));
    $('#xout')[0].innerHTML = "<a href='#map-anchor'>&#x02A02</a>";
    $('#xout').on("click", function() {resetMapInfo()})

    $("<li>").attr("id","school-name").appendTo(schoolListing);
    $("#school-name")[0].innerHTML = '<h1>' + properties['name'] + '</h1>';
    
    if (properties['img']) {
        $("<li>").attr("id","school-pic").appendTo(schoolListing);
        $("#school-pic")[0].innerHTML = '<img src="' + properties['img'] + '" />';
    }

    $('#legend').before($("<ul>").attr("id","school-listing"));

    $("<li>").attr("id","school-address").appendTo(schoolListing);
    $("#school-address")[0].innerText = properties['address'] + " (" + properties['comm_area'] + ")";
 
    $("<li>").attr("id","school-alderman").appendTo(schoolListing);
    $("#school-alderman")[0].innerText = properties['alderman'];
    

    //docs    
    $("<li>").attr("id","school-docs").appendTo(schoolListing);
    status_doc = null;
    if (properties['status_doc'].length) {
        $("#school-docs")[0].innerHTML = "<a href='" + properties['status_doc'] + "'>Status doc</a> &#124; ";
    }
    $("#school-docs")[0].innerHTML += "<a href='" + properties['repurpose_doc'] + "'>Repurposing doc</a>";
    

    //narratives
    $("<li>").attr("id","school-narrative").appendTo(schoolListing);
    $("#school-narrative")[0].innerText = properties['narrative'];

    //share
    $("<li>").attr("id","school-share").appendTo(schoolListing);
    $("<span>").attr("id","school-tweet").appendTo($("#school-share"));
    tweet_text = "What's happened to " + properties['name'] + " school since CPS closed it in 2013? "
    tweet_text += window.location.href
    tweet_text += ' via @chicagoreporter'
    twttr.widgets.createShareButton(
        '/',
        document.getElementById('school-tweet'),
        {text: tweet_text,}
    );

    $("<span>").attr("id","fb-share-button").appendTo($("#school-share"));
    $("#fb-share-button")[0].innerHTML = "<a href='#'>Share</a>";
    $("#fb-share-button").on("click", function() {
        FB.ui({
            method: 'share',
            href: 'http://chicagoreporter.com',
            quote: tweet_text,
            layout: 'button',
        }, function(response){}
        )
    });

    resize = false;
    // resize text if too long
    // TODO: fix way we measure share button height
    while($("#school-share").offset().top + 50 > $("#legend").children('hr').offset().top) {
        size = parseInt($("#school-address").css("font-size"),10);
        debug_data = {'school-share.top':$("#school-share").offset().top,'school-share.height':$("#school-share").height(), 'legend.top': $("#legend").children('hr').offset().top,'size':size}
        $("#school-address").css("font-size",size-1);
        $("#school-alderman").css("font-size",size-1);
        $("#school-docs").css("font-size",size-1);
        $("#school-narrative").css("font-size",size-1);
        console.log(debug_data)
        console.log($("#school-share").offset().top + 50 > $("#legend").children('hr').offset().top)
        console.log([$("#school-share").offset().top, 50, $("#legend").children('hr').offset().top])
    }

    //TODO: fix infinite recursion 
    /*
    while($("#school-name").offset().left + $("#school-name").parent()[0].scrollWidth > $("#infobox").offset().left + $("#infobox").width()){
        hedsize = parseInt($("#school-name").css("font-size"),10);
        $("#school-name").css("font-size",hedsize-1);
        console.log('resize hed');
    }
    */
}


status_icons = {
    'sold': 'sold_school-15',
    'for sale': 'unsold_school-15',
    'repurposed': 'repurposed_school-15'
};

