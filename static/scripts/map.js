var locationColumn = 'latitude';
var map, layer;
var now, midnight, midnight1, midnight7;

var state = {

    // methods acting on the state object

    parseHashStringIntoState: function() {
        var hash = window.location.hash;
        var map, timeframe, tags, view, location, event;
        var strings = hash.replace(/^#/,'').split('/');
        for (var i=0; i<strings.length; i++) {
            var s = strings[i];
            if (!map && s.match(/\d+\.\d+,\d+\.\d+,\d+z,\d+px/))
                map = s;
            else if (!timeframe && s.match(/now|today|tomorrow|week|all/)) 
                timeframe = s;
            else if (!tags && !s.match(/marker|location|list|event/))
                tags = s;
            else if (!view && s.match(/marker|location|list|event/))
                view = s;
            else if (view && view.match(/marker|location/))
                location = s;
            else if (view && view.match(/event/))
                event = s;
        }
        if (map) {
            var coords = map.split(',');
            this.lat = parseFloat(coords[0]);
            this.lon = parseFloat(coords[1]);
            this.zoom = parseInt(coords[2].replace(/z/,''));
            this.port = parseInt(coords[3].replace(/px/,'')); // having this value is also used as an indicator
                                                              // that the coordinates were provided in the URL
        } else {
            this.lat = 51.213282784793925; // default
            this.lon = 4.427805411499094; // default
            this.zoom = 13; // default
        }
        if (timeframe) {
            this.timeframe = timeframe;
        } else {
            this.timeframe = 'week'; // default
        }
        if (tags) {
            this.tags = tags.split(',');
        } else {
            this.tags = []; // default
        }
        this.view = view;
        this.location = location;
        this.event = event;
    },
    getMapCenterpointAndSet: function() {
        var loc = map.getCenter();
        this.lat = loc.lat();
        this.lon = loc.lng();
    },
    setCenterpoint: function(lat,lon) {
        this.lat = lat;
        this.lon = lon;
    },
    getMapZoomAndSet: function() {
        var zoom = map.getZoom();
        this.zoom = zoom;
    },
    setTimeframe: function(timeframe) {
        this.timeframe = timeframe;
    },
    toggleTagInList: function(tag) {
        var i;
        if ((i = $.inArray(tag, this.tags)) > -1 ) {
            // tag active
            this.tags.splice(i,1); // remove tag
        } else {
            // tag not active
            this.tags.push(tag); // add tag
        }
    },

    // methods acting on the hash string

    generateNewHashString: function() {
        var map, timeframe, tags, view, location, event;
        map = this.lat.toFixed(6) + ',' + this.lon.toFixed(6);
        map += ',' + this.zoom + 'z';
        var mapDiv = $('#map-canvas');
        map += ',' + Math.min(mapDiv.height(), mapDiv.width()) + 'px';
        timeframe = this.timeframe;
        tags = this.tags.join(',');
        view = this.view;
        location = this.location;
        event = this.location;
        var hash = '#' + map;
        if (timeframe)
            hash += '/' + timeframe;
        if (tags)
            hash += '/' + tags;
        if (view)
            hash += '/' + view;
        if (location)
            hash += '/' + location;
        if (event)
            hash += '/' + event;
        window.location.hash = hash;
    },

    // methods acting on the fusion table query

    generateNewQueryString: function() {
        var timeframe = this.timeframe;
        var tags = this.tags;
        var query;
        if (timeframe == 'now')
        // start < now and end > now
            query = "start < '" + now + "' and end > '" + now + "'";
        else if (timeframe == 'today')
        // start > now and start < midnight
            query = "start > '" + now + "' and start < '" + midnight + "'";
        else if (timeframe == 'tomorrow')
        // start > midnight and start < midnight + 1 day
            query = "start > '" + midnight + "' and start < '" + midnight1 + "'";
        else if (timeframe == 'week')
        // start > now and start < midnight + 7 days
            query = "start > '" + midnight + "' and start < '" + midnight7 + "'";
        else if (timeframe == 'all')
        // start > now
            query = "start > '" + now + "'";
        for (var i = 0; i < tags.length; i++) {
            query += " AND tags CONTAINS '#" + tags[i] + "#'";
            // tags in the fusion table are surrounded by hash characters to avoid
            // confusion if one tag would be a substring of another tag
        }
        layer.setOptions({
            query: {
                select: locationColumn,
                from: tableId,
                where: query
            }
        });
    },

    // methods acting on the GUI (map, buttons, ...)

    setMapCenterpoint: function(lat, lon) {
        var loc = new google.maps.LatLng(lat, lon);
        map.setCenter(loc);
    },
    setMapZoom: function(zoom) {
        map.setZoom(zoom);
        this.zoom = zoom;
    },
    highlightTimeframeButton: function(timeframe) {
        $('#timeframe span').removeClass('active');
        $('#' + timeframe).addClass('active');
    },
    toggleTagButton: function(tag) {
        if ($('#' + tag).hasClass('active')) {
            // tag active
            $('#' + tag).removeClass('active');
        } else {
            // tag not active
            $('#' + tag).addClass('active');
        }
    },
    disableAllTagButtons: function() {
        $('#tags span').removeClass('active');
    },

    panDirty: false, // dirty flag when map is being panned
    zoomDirty: false // dirty flag when map is zoomed
};

// parse the hash; the coordinates are used by the google map initialization
state.parseHashStringIntoState();

// start syncing the reference times
updateNowAndMidnight();

// google maps initialization function
function initialize() {
    google.maps.visualRefresh = true; // enable new look for Google Maps
    var mapDiv = document.getElementById('map-canvas');
    map = new google.maps.Map(mapDiv, {
        center: new google.maps.LatLng(state.lat, state.lon),
        zoom: state.zoom,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        mapTypeControl: false,
        panControl: false,
        zoomControl: true,
        zoomControlOptions: {
          style: google.maps.ZoomControlStyle.LARGE,
          position: google.maps.ControlPosition.LEFT_CENTER
        },
        scaleControl: false,
        streetViewControl: false
    });

    layer = new google.maps.FusionTablesLayer({
        map: map,
        heatmap: {
            enabled: false
        },
        query: {
            select: locationColumn,
            from: tableId,
            where: "start > '" + now + "'" // default filter, relies on global timeframe filter variable !!
        },
        styles: [{
            markerOptions: {
               iconName: "large_green"
            }
         }],
        options: {
            styleId: 2,
            templateId: 2,
            suppressInfoWindows: true
        }
    });

    // re-center the map if a geo position is available and no coordinates were in the URL
    if (!state.port && navigator.geolocation) {
        browserSupportFlag = true;
        navigator.geolocation.getCurrentPosition(function (position) {
            state.setCenterpoint(position.coords.latitude, position.coords.longitude);
            state.setMapCenterpoint(position.coords.latitude, position.coords.longitude);
            state.generateNewHashString();
        });
    }

    google.maps.event.addListener(map, 'drag', function() {
        state.panDirty = true;
    })

    google.maps.event.addListener(map, 'zoom_changed', function() {
        state.zoomDirty = true;
    })

    google.maps.event.addListener(map, 'idle', function() {
        if (state.panDirty) {
            state.getMapCenterpointAndSet();
            state.generateNewHashString();
            state.panDirty = false;
        }
        if (state.zoomDirty) {
            state.getMapZoomAndSet();
            state.generateNewHashString();
            state.zoomDirty = false;
        }
    })

    return;
}

// call the google map initialization function (no need to wait for jQuery!)
google.maps.event.addDomListener(window, 'load', initialize);

// jQuery ready
$(document).ready(function() {

    state.highlightTimeframeButton(state.timeframe);
    for (var i=0; i<state.tags.length; i++) {
        state.toggleTagButton(state.tags[i]);
    }

    // add event handlers to the timeframe buttons
    $('#timeframe').on("click", "span", function() {
        state.setTimeframe(this.id);
        state.generateNewQueryString();
        state.generateNewHashString();
        state.highlightTimeframeButton(this.id);
    });

    // create the tag buttons
    $.each(tags.split(','), function(index, tag) {
        $('<span/>',{id: slugify(tag)}).text(tag).appendTo('#tags');
    })

    $('#tags').on("click", "span", function() {
        state.toggleTagInList(this.id);
        state.generateNewQueryString();
        state.generateNewHashString();
        state.toggleTagButton(this.id);
    });

    window.onhashchange = function() {
        state.parseHashStringIntoState();
        state.generateNewQueryString();
        state.setMapCenterpoint(state.lat,state.lon);
        state.setMapZoom(state.zoom);
        state.highlightTimeframeButton(state.timeframe);
        state.disableAllTagButtons();
        for (var i=0; i<state.tags.length; i++) {
            state.toggleTagButton(state.tags[i]);
        }
    };

    return;
});

function slugify(str) {
    str = str.replace(/^\s+|\s+$/g, ''); // trim
    str = str.toLowerCase();
    var from = "ãàáäâẽèéëêìíïîõòóöôùúüûñç·/_,:;";
    var to = "aaaaaeeeeeiiiiooooouuuunc------";
    for (var i = 0, l = from.length; i < l; i++) {
        str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
    }
    str = str.replace(/[^a-z0-9 -]/g, '') // remove invalid chars
        .replace(/\s+/g, '-') // collapse whitespace and replace by -
        .replace(/-+/g, '-'); // collapse dashes
    return str;
}

// helper function for updating a set of global variables each minutes,
// used when filtering the fusion table on timeframe
function updateNowAndMidnight() {
    function format(date) {
        // day = 0 for Sunday, 1 for Monday etc...
        var yyyy = date.getFullYear();
        var mm = date.getMonth() + 1;
        var dd = date.getDate();
        var hours = date.getHours();
        var minutes = date.getMinutes();
        if (dd < 10) {dd = '0' + dd};
        if (mm < 10) {mm = '0' + mm};
        if (hours < 10) {hours = '0' + hours};
        if (minutes < 10) {minutes = '0' + minutes};
        var s = yyyy + '-' + mm + '-' + dd + ' ' + hours + ':' + minutes + ':00';
        return s;
    }
    var now_d = new Date();
    var midnight_d = now_d;
    midnight_d.setDate(midnight_d.getDate() + 1);
    midnight_d.setHours(0);
    midnight_d.setMinutes(0);
    var midnight1_d = midnight_d;
    midnight1_d.setDate(midnight1_d.getDate() + 1);
    var midnight7_d = midnight_d;
    midnight7_d.setDate(midnight7_d.getDate() + 7);
    // update the global vars
    now = format(now_d);
    midnight = format(midnight_d);
    midnight1 = format(midnight1_d);
    midnight7 = format(midnight7_d);
    // from now on, update every minute
    setTimeout(updateNowAndMidnight, 60000);
    return;
}

