var locationColumn = 'latitude';
var map, layer;
var now, midnight, midnight1, midnight7;

var state = {

    // methods acting on the state object

    parseHashStringIntoState: function() {
        var hash = window.location.hash;
        var map, timeframe, tags, hashtags, view, location, event, datetime;
        var strings = hash.replace(/^#/,'').split('/');
        for (var i=0; i<strings.length; i++) {
            var s = strings[i];
            if (!map && s.match(/\d+\.\d+,\d+\.\d+,\d+z,\d+px/))
                map = s;
            else if (!view && s.match(/location|list|event/))
                view = s;
            else if (s.match(/hash/)) {
                if (i++ < strings.length)
                    hashtags = strings[i];
            }
            else if (view && view.match(/location/))
                location = s;
            else if (view && view.match(/event/)) {
                event = s;
                if (i++ < strings.length)
                    datetime = strings[i];
            }
            else if (!timeframe && s.match(/now|today|tomorrow|week|all/))
                timeframe = s;
            else if (!tags && !s.match(/marker|location|list|event/))
                tags = s;
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
            this.timeframe = 'all'; // default
        }
        if (tags) {
            this.tags = tags.split(',');
        } else {
            this.tags = []; // default
        }
        if (hashtags) {
            this.hashtags = hashtags.split('.');
        } else {
            this.hashtags = []; // default
        }
        this.view = view;
        this.location = location;
        this.event = event;
        this.datetime = datetime;
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
        this.tags = [];
        // the following code supports selections of multiple tags,
        // but the GUI doesn't support this, therefor the array is reset!
        // this should be cleaned up when definitively giving up multiple tag querying
        var i;
        if ((i = $.inArray(tag, this.tags)) > -1 ) {
            // tag active
            this.tags.splice(i,1); // remove tag
        } else {
            // tag not active
            if (tag != 'all-tags') {
                this.tags.push(tag); // add tag
            } else {
                this.tags = [];
            }
        }
    },
    toggleHashtagInList: function(hashtag) {
        this.hashtags = [];
        // the following code supports selections of multiple tags,
        // but the GUI doesn't support this, therefor the array is reset!
        // this should be cleaned up when definitively giving up multiple tag querying
        var i;
        if ((i = $.inArray(slugify(hashtag), this.hashtags)) > -1 ) {
            // tag active
            this.hashtags.splice(i,1); // remove tag
        } else {
            // tag not active
            if (hashtag != '') {
                this.hashtags.push(slugify(hashtag)); // add tag
            } else {
                this.hashtags = [];
            }
        }
    },
    setViewLocation: function(location_slug) {
        this.view = 'location';
        this.location = location_slug;
    },
    setViewMap: function() {
        this.view = 'map';
    },
    setViewEvent: function(event_slug, datetime_slug) {
        this.view = 'event';
        this.event = event_slug;
        this.datetime = datetime_slug;
    },

    // methods acting on the hash string

    generateNewHashString: function() {
        var map, timeframe, tags, hashtags, view, location, event, datetime;
        map = this.lat.toFixed(6) + ',' + this.lon.toFixed(6);
        map += ',' + this.zoom + 'z';
        var mapDiv = $('#map-canvas');
        map += ',' + Math.min(mapDiv.height(), mapDiv.width()) + 'px';
        timeframe = this.timeframe;
        tags = this.tags.join(',');
        hashtags = this.hashtags.join(',');
        view = this.view;
        location = this.location;
        event = this.event;
        datetime = this.datetime;
        var hash = '#' + map;
        if (timeframe)
            hash += '/' + timeframe;
        if (tags)
            hash += '/' + tags;
        if (hashtags)
            hash += '/hash/' + hashtags;
        if (view && view !== 'map')
            hash += '/' + view;
        if (view == 'location' && location)
            hash += '/' + location;
        if (view == 'event' && event) {
            hash += '/' + event;
            if (datetime)
                hash += '/' + datetime;
        }
        this.ignoreHashChange = true;
        window.location.hash = hash;
    },

    // methods acting on the fusion table query

    generateNewQueryString: function() {
        var timeframe = this.timeframe;
        var tags = this.tags;
        var hashtags = this.hashtags;
        var query;
        if (timeframe == 'now')
        // start < now and end > now
            query = "start < '" + now + "' AND end > '" + now + "'";
        else if (timeframe == 'today')
        // start > now and start < midnight
            query = "start > '" + now + "' AND start < '" + midnight + "'";
        else if (timeframe == 'tomorrow')
        // start > midnight and start < midnight + 1 day
            query = "start > '" + midnight + "' AND start < '" + midnight1 + "'";
        else if (timeframe == 'week')
        // start > now and start < midnight + 7 days
            query = "start > '" + midnight + "' AND start < '" + midnight7 + "'";
        else if (timeframe == 'all')
        // start > now
            query = "start > '" + now + "'";
        for (var i = 0; i < tags.length; i++)
            query += " AND tags CONTAINS '#" + tags[i] + "#'";
        for (var i = 0; i < hashtags.length; i++)
            query += " AND hashtags CONTAINS '#" + hashtags[i] + "#'";
            // tags in the fusion table are surrounded by hash characters to avoid
            // confusion if one tag would be a substring of another tag
        if (limit)
            query += " AND start < '" + limit + "'";
        layer.setOptions({
            query: {
                select: locationColumn,
                from: tableId,
                where: query
            }
        });
    },
    highlightLocationMarker: function() {
        if (state.view == 'location') {
            layer.set('styles', [{
                markerOptions: {
                    iconName: "placemark_circle"
                }
            },
            {
                where: "'location slug' = '" + state.location + "'",
                markerOptions: {
                    iconName: "placemark_circle_highlight"
                }
            }]);
        } else if (state.view == 'event') {
            layer.set('styles', [{
                markerOptions: {
                    iconName: "placemark_circle"
                }
            },
                {
                    where: "'event slug' = '" + state.event + "'",
                    markerOptions: {
                        iconName: "placemark_circle_highlight"
                }
            }]);
        } else {
            layer.set('styles', [{
                markerOptions: {
                    iconName: "placemark_circle"
                }
            }]);
        }
    },

    // methods acting on the GUI (map, buttons, ...)

    setMapCenterpoint: function() {
        var loc = new google.maps.LatLng(this.lat, this.lon);
        map.setCenter(loc);
    },
    setMapZoom: function() {
        map.setZoom(this.zoom);
    },
    highlightTimeframeButton: function() {
        $('#timeframe-button').attr("class","action-button timeframe").addClass(this.timeframe);
        // copy the day on the calendar icon (if any)
        $('#timeframe-button').html($('#timeframe-menu #' + this.timeframe + ' .menu-icon').html());
    },
    highlightTagButtons: function() {
        var tag = this.tags.length > 0 ? this.tags[0] : 'all-tags';
        $('.menu-item.tags').removeClass("menu-item-label");
        $('.menu-item.tags#' + tag).addClass("menu-item-label");
        $('#tags-button').attr("class","action-button tags").addClass(tag_colors[tag]);
    },
    highlightHashtagButton: function() {
        if (this.hashtags.length > 0) {
            $('#hash-button').removeClass("action-button-hash-white");
            $('#hash-button').addClass("action-button-hash-bluegray");
            if (! $('hash-menu input').val())
                // avoid overwriting a plain hashtag with the slugified one
                $('#hash-menu input').val(this.hashtags[0]);
        } else {
            $('#hash-button').removeClass("action-button-hash-bluegray");
            $('#hash-button').addClass("action-button-hash-white");
            $('#hash-menu input').val('');
        }
    },
    displayIFrame: function() {
        $('#iframe iframe').remove(); // removing the iframe to not make it part of browser history
        if (this.view == 'location' || this.view == 'list' || this.view == 'event') {
            // compose the URL for the iframe (TODO: update for other views than location)
            var url = window.location.protocol + "//" + window.location.host;
            if (this.view)
                url += '/' + this.view;
            if (this.view == 'location' && this.location)
                url += '/' + this.location;
            if (this.view == 'event' && this.event) {
                url += '/' + this.event;
                if (this.datetime)
                    url += '/' + this.datetime;
            }
            if (this.view !== 'event' && this.timeframe)
                url += '/' + this.timeframe;
            var tags = this.tags.join(',');
            if (this.view !== 'event' && tags)
                url += '/' + tags;
            var hashtags = this.hashtags.join(',');
            if (this.view !== 'event' && hashtags)
                url += '/' + hashtags;
            // append the ?id= parameter if present in the location, just for debugging on localhost
            // and also append the client timestamp
            if (location.search) {
                url += location.search;
                url += '&';
            } else {
                url += '?';
            }
            url += 'now=' + now;
            // set the URL and display the iframe
            $('<iframe/>').appendTo('#iframe');
            $('#iframe iframe').attr('src', url);
            $('#iframe').show();

        } else {
            $('#iframe').hide();
        }
    },
    displayQrIcon: function() {
        if (this.view == 'location') {
            var url = window.location.protocol + "//" + window.location.host + '/qr';
            if (this.view)
                url += '/' + this.view;
            if (this.view == 'location' && this.location)
                url += '/' + this.location;
            // append the ?id= parameter if present in the location, just for debugging on localhost
            url += window.location.search;
            $('#qr a').attr('href', url);
            $('#qr').show();
        } else {
            $('#qr').hide();
        }
    },
    displayAddEventIcon: function() {
        var url = window.location.protocol + "//" + window.location.host + '/new';
        if (this.view == 'event') {
            // append the event slug
            url += '/' + this.event;
        } else if (this.view == 'location') {
            // append the location slug
            url += '/location/' + this.location;
        }
        // append the ?id= parameter if present in the location, just for debugging on localhost
        url += window.location.search;
        $('#add a').attr('href', url);
        $('#add').show(); // right now, there are no states where it should be hidden
    },
    displayModifyEventIcon: function() {
        if (this.view == 'event') {
            var url = window.location.protocol + "//" + window.location.host + '/update';
            // append the event slug
            url += '/' + this.event;
            // append the ?id= parameter if present in the location, just for debugging on localhost
            url += window.location.search;
            $('#modify a').attr('href', url);
            $('#modify').show();
        } else {
            $('#modify').hide();
        }
    },


    // attributes

    panDirty: false, // dirty flag when map is being panned
    zoomDirty: false, // dirty flag when map is zoomed
    ignoreHashChange: false // used to ignore hash changes triggered by myself
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
          style: google.maps.ZoomControlStyle.SMALL,
          position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
        scaleControl: false,
        streetViewControl: false
    });

    layer = new google.maps.FusionTablesLayer({
        map: map,
        heatmap: {
            enabled: false
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

    state.generateNewQueryString();
    state.highlightLocationMarker();

    // re-center the map if a geo position is available and no coordinates were in the URL
    if (!state.port && navigator.geolocation) {
        browserSupportFlag = true;
        navigator.geolocation.getCurrentPosition(function (position) {
            state.setCenterpoint(position.coords.latitude, position.coords.longitude);
            state.setMapCenterpoint();
            state.generateNewHashString();
        });
    }

    google.maps.event.addListener(map, 'drag', function() {
        state.panDirty = true;
    });

    google.maps.event.addListener(map, 'zoom_changed', function() {
        state.zoomDirty = true;
    });

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
    });

    google.maps.event.addListener(layer, 'click', function(e) {
        state.setViewLocation(e.row['location slug'].value);
        state.generateNewHashString();
        state.displayIFrame();
        state.highlightLocationMarker();
        state.displayQrIcon();
        state.displayAddEventIcon();
        state.displayModifyEventIcon();
    });

    return;
}

// call the google map initialization function (no need to wait for jQuery!)
google.maps.event.addDomListener(window, 'load', initialize);

// jQuery ready
$(document).ready(function() {

    state.highlightTimeframeButton();
    state.highlightTagButtons();
    state.highlightHashtagButton();
    state.displayIFrame();
    state.displayQrIcon();
    state.displayAddEventIcon();
    state.displayModifyEventIcon();

    // add the timeframe menu items, and hide based on now, midnight, midnight1 and midnight7
    if (limit < midnight7) {
        $("a.menu-item-week").hide();
        if (limit < midnight1) {
            $("a.menu-item-tomorrow").hide();
        }
    }

    // add event handlers to the action buttons
    $('#timeframe-button').on("click", function() {
        $('#tags-menu,#hash-menu').hide();
        $('#timeframe-menu').toggle();
    })
    $('#tags-button').on("click", function() {
        $('#timeframe-menu,#hash-menu').hide();
        $('#tags-menu').toggle();
    })
    $('#hash-button').on("click", function() {
        $('#timeframe-menu,#tags-menu').hide();
        $('#hash-menu').toggle();
    })

    // add event handlers to the timeframe buttons
    $('#timeframe-menu').on("click", "a", function() {
        $('#timeframe-menu').hide();
        state.setTimeframe(this.id);
        state.generateNewQueryString();
        state.generateNewHashString();
        state.highlightTimeframeButton();
        state.displayIFrame();
    });

    $('#tags-menu').on("click", "a", function() {
        $('#tags-menu').hide();
        state.toggleTagInList(this.id);
        state.generateNewQueryString();
        state.generateNewHashString();
        state.highlightTagButtons();
        state.displayIFrame();
    });

    $('#hash-menu').on("click", "a.search-button", function() {
        $('#hash-menu').hide();
        state.toggleHashtagInList($('#hash-menu input').val());
        state.generateNewQueryString();
        state.generateNewHashString();
        state.highlightHashtagButton();
        state.displayIFrame();
    });

    $("#hash-menu input").keyup(function(event){
        if(event.keyCode == 13) {
            $("#hash-menu a.search-button").click();
        }
    });

    $('#hash-menu').on("click", "a.search-reset-button", function() {
        $('#hash-menu input').val('');
    });

    window.onhashchange = function() {
        if (state.ignoreHashChange) {
            state.ignoreHashChange = false;
        } else {
            state.parseHashStringIntoState();
            state.generateNewQueryString();
            state.setMapCenterpoint();
            state.setMapZoom();
            state.highlightTimeframeButton();
            state.highlightTagButtons();
            state.highlightHashtagButton();
            state.displayIFrame();
            state.highlightLocationMarker();
            state.displayQrIcon();
            state.displayAddEventIcon();
            state.displayModifyEventIcon();
        }
    };

    return;
});

function on_click_static_map_in_iframe() {
    // callable from within iframe
    state.setViewMap();
    state.generateNewHashString();
    state.displayIFrame();
    state.highlightLocationMarker();
    state.displayQrIcon();
    state.displayAddEventIcon();
    state.displayModifyEventIcon();
    return;
}

function on_click_event_in_iframe(event_slug, datetime_slug) {
    // callable from within iframe
    state.setViewEvent(event_slug, datetime_slug);
    state.generateNewHashString();
    state.displayIFrame();
    state.displayAddEventIcon();
    state.displayModifyEventIcon();
    return;
}

function on_body_resize_in_iframe() {
    // callable from within iframe
    // this is not affecting the state object
    // it resizes the iframe and it's containing div
    // but only in desktop views OR when the class 'variable_height' is set
    var height = $('#iframe iframe').contents().find('body').height();
    if ($('#iframe').css('position') !== 'fixed' || $('#iframe').hasClass('variable_height')) {
        $('#iframe').css('height', height);
        $('#iframe iframe').css('height', height);  // strange behaviour otherwise
    }
    return;
}

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
// used when filtering the fusion table on timeframe and
// as part of the iframe URL to provide the server with client time
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
    var d = new Date();
    now = format(d);
    d.setDate(d.getDate() + 1);
    d.setHours(0);
    d.setMinutes(0);
    midnight = format(d);
    d.setDate(d.getDate() + 1);
    midnight1 = format(d);
    d.setDate(d.getDate() + 7);
    midnight7 = format(d);
    // from now on, update every hour (this value is in the iframe URL because the server only knows
    // server time, and if the frequency would be increased, the browser caching wouldn't make
    // much sense)
    setTimeout(updateNowAndMidnight, 3600000);
    return;
}

