var map;
var ajaxrequest;
var loaded_tiles = [];
var precision = 4;

// hidden feature:
var styles = {
    'default': [{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]}],
    'sobr': [{"featureType":"all","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"administrative.country","elementType":"all","stylers":[{"visibility":"on"}]},{"featureType":"road.highway","elementType":"geometry","stylers":[{"visibility":"simplified"},{"lightness":98}]},{"featureType":"water","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"all","stylers":[{"visibility":"on"},{"weight":1},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"all","stylers":[{"visibility":"on"},{"lightness":55}]}],
    'night0': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -0 },{"gamma": 1 },{"lightness": -0 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night1': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -10 },{"gamma": 0.90 },{"lightness": -10 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night2': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -20 },{"gamma": 0.80 },{"lightness": -20 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night3': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -30 },{"gamma": 0.70 },{"lightness": -30 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night4': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -40 },{"gamma": 0.60 },{"lightness": -40 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night5': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -50 },{"gamma": 0.50 },{"lightness": -50 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night6': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -60 },{"gamma": 0.40 },{"lightness": -60 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}],
    'night7': [{"featureType":"all","elementType":"all","stylers": [{"saturation": -70 },{"gamma": 0.30 },{"lightness": -70 }]},{"featureType":"road.highway","elementType":"labels","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"geometry","stylers":[{"visibility":"simplified"}]},{"featureType":"administrative.province","elementType":"geometry","stylers":[{"visibility":"on"},{"weight":2},{"saturation":-100},{"lightness":-100}]},{"featureType":"administrative.locality","elementType":"labels","stylers":[{"visibility":"off"}]}]
};

// https://tc39.github.io/ecma262/#sec-array.prototype.includes
if (!Array.prototype.includes) {
  Object.defineProperty(Array.prototype, 'includes', {
    value: function(searchElement, fromIndex) {

      // 1. Let O be ? ToObject(this value).
      if (this == null) {
        throw new TypeError('"this" is null or not defined');
      }

      var o = Object(this);

      // 2. Let len be ? ToLength(? Get(O, "length")).
      var len = o.length >>> 0;

      // 3. If len is 0, return false.
      if (len === 0) {
        return false;
      }

      // 4. Let n be ? ToInteger(fromIndex).
      //    (If fromIndex is undefined, this step produces the value 0.)
      var n = fromIndex | 0;

      // 5. If n ≥ 0, then
      //  a. Let k be n.
      // 6. Else n < 0,
      //  a. Let k be len + n.
      //  b. If k < 0, let k be 0.
      var k = Math.max(n >= 0 ? n : len - Math.abs(n), 0);

      // 7. Repeat, while k < len
      while (k < len) {
        // a. Let elementK be the result of ? Get(O, ! ToString(k)).
        // b. If SameValueZero(searchElement, elementK) is true, return true.
        // c. Increase k by 1.
        // NOTE: === provides the correct "SameValueZero" comparison needed here.
        if (o[k] === searchElement) {
          return true;
        }
        k++;
      }

      // 8. Return false
      return false;
    }
  });
}

var state = {

    // methods acting on the state object

    parseHashStringIntoState: function() {
        var hash = decodeURIComponent(History.getState().hash).split('?')[0];
        if (window.location.hash) hash = window.location.hash.replace(/^#/,''); // to make the old links work
        var coordinates, timeframe, tags, hashtags, view, location, event, datetime;
        var strings = hash.split('/');
        for (var i=0; i<strings.length; i++) {
            var s = strings[i];
            if (!coordinates && s.match(/-?\d+\.\d+,-?\d+\.\d+,\d+z,\d+px/))
                coordinates = s;
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
        if (coordinates) {
            this.locationInUrl = true;
            var coords = coordinates.split(',');
            this.lat = parseFloat(coords[0]);
            this.lon = parseFloat(coords[1]);
            this.zoom = parseInt(coords[2].replace(/z/,''));
            this.port = parseInt(coords[3].replace(/px/,'')); // having this value is also used as an indicator
                                                              // that the coordinates were provided in the URL
        } else {
            this.locationInUrl = false;
            if (default_latitude)
                this.lat = default_latitude;
            else
                this.lat = 51.213282784793925; // default
            if (default_longitude)
                this.lon = default_longitude;
            else
                this.lon = 4.427805411499094; // default
            if (default_zoom && default_zoom != 'NaN' && default_zoom > 0)
                this.zoom = parseInt(default_zoom);
            else
                this.zoom = 15; // default
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
        this.location = null;  // otherwise an old value may interfere with marker highlighting
    },
    setViewEvent: function(event_slug, datetime_slug) {
        this.view = 'event';
        this.event = event_slug;
        this.datetime = datetime_slug;
        this.location = null;  // otherwise an old value may interfere with marker highlighting
    },
    setLocation: function(location_slug) {
        // this is the location that comes from the iframe and is used for highlighting
        // all markers on that location in case of event view
        if (this.view == 'event') {
            this.location = location_slug;
        }
    },

    // methods acting on the hash string

    generateNewHashString: function() {
        var map, timeframe, tags, hashtags, view, location, event, datetime;
        map = parseFloat(this.lat).toFixed(6) + ',' + parseFloat(this.lon).toFixed(6);
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
        var hash = '/' + map;
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
        // append the ?id= parameter if present in the location, just for debugging on localhost
        if (window.location.search)
            hash += window.location.search;
        this.locationInUrl = true;
        this.ignoreHashChange = true;
        History.pushState(null,$(document).attr('title'),hash)  // title remains unchanged
    },

    // methods acting on the maps data layer

    loadGeoJSON: function() {
        // calculate the list of tiles in the viewport
        var new_tiles = viewport_tiles(precision);
        // subtract the loaded tiles
        new_tiles = subtract(new_tiles, loaded_tiles);
        //console.log("new tiles in viewport: " + new_tiles.length + " : " + new_tiles.toString());
        if (new_tiles.length > 12 && precision > 1) {
            precision = precision - 1;
            //console.log("SWITCHING TO PRECISION " + precision);
            var parent_tiles = parent(loaded_tiles);
            //console.log("parent tiles: " + parent_tiles.length + " : " + parent_tiles.toString());
            var missing_tiles = complement(parent_tiles, loaded_tiles);
            //console.log("missing tiles: " + missing_tiles.length + " : " + missing_tiles.toString());
            missing_tiles.forEach(function(tile) {
                map.data.loadGeoJson(geojson_url(tile));
            });
            loaded_tiles = parent_tiles;
            new_tiles = subtract(viewport_tiles(precision), loaded_tiles);
            //console.log("new tiles in viewport: " + new_tiles.length + " : " + new_tiles.toString());
        }
        // load geojson for the tiles (using forEach as a closure for the tile variable)
        new_tiles.forEach(function(tile) {
            map.data.loadGeoJson(geojson_url(tile));
        });
        loaded_tiles = loaded_tiles.concat(new_tiles);
    },

    visibleFeatures: function() {
        // applies filtering and highlights the selected location
        var timeframe = this.timeframe;
        var tags = this.tags;
        var hashtags = this.hashtags;
        var set_style = function(feature) {
            // evaluate timeframe
            var visibility = (timeframe == 'all') ||
                (timeframe == 'now' && feature.getProperty('now')) ||
                (timeframe == 'today' && feature.getProperty('today')) ||
                (timeframe == 'tomorrow' && feature.getProperty('tomorrow')) ||
                (timeframe == 'week' && feature.getProperty('week'));
            // evaluate tags (make invisible if any item in tags is not in feature.getProperty('tags'))
            for (var i = 0; i < tags.length; i++) {
                if (!feature.getProperty('tags').includes(tags[i]))
                    visibility = false;
            }
            // evaluate hashtags (make invisible if any item in hashtags is not in feature.getProperty('hashtags'))
            for (var i = 0; i < hashtags.length; i++) {
                if (!feature.getProperty('hashtags').includes(hashtags[i]))
                    visibility = false;
            }
            // check if the location should be highlighted
            if (state.location == feature.getProperty('location slug'))
                var url = window.location.protocol + "//" + window.location.host + '/images/map-marker-highlighted.png';
            else
                var url = window.location.protocol + "//" + window.location.host + '/images/map-marker.png';
            return {
                visible: visibility,
                icon: {
                    url: url,
                    scaledSize: new google.maps.Size(24, 24),
                    anchor: new google.maps.Point(12, 12),
                    cursor: "pointer"
                }
            };
        };
        map.data.setStyle(set_style);
    },

    // methods acting on the GUI (map, buttons, ...)

    setMapCenterpoint: function() {
        var loc = new google.maps.LatLng(this.lat, this.lon);
        state.ignoreMapEvents = true;
        map.setCenter(loc);
    },
    setMapZoom: function() {
        state.ignoreMapEvents = true;
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
        if (this.view == 'location' || this.view == 'list' || this.view == 'event') {
            $('#cardframe').show();
            $('#loading').css('display','block');
            // compose the URL for the iframe (TODO: update for other views than location)
            var url = window.location.protocol + "//" + window.location.host + '/card';
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
                url += '/hash/' + hashtags;
            // append the ?id= parameter if present in the location, just for debugging on localhost
            // and also append the client timestamp
            if (window.location.search) {
                url += window.location.search;
                url += '&';
            } else {
                url += '?';
            }
            //url += 'now=' + encodeURIComponent(now);
            // load the URL via ajax and display the contents
            if (typeof ajaxrequest !== 'undefined')
                ajaxrequest.abort();
            ajaxrequest = $.ajax(url, {  // I could use .load() with page fragments here, but it doesn't return the request
                type: 'GET',
                dataType: 'html'
            }).done(function (response) {
                $('#tempcardholder').html(response);
                $('#cardholder').html($('#tempcardholder').find(".card"));
                $('#cardframe').show();
                $('#loading').css('display','none');
                on_location_known_in_iframe();
                on_location_slug_known_in_iframe();
                on_iframe_data_displayed();
            });
        } else {
            if (typeof ajaxrequest !== 'undefined')
                ajaxrequest.abort();
            $('#cardholder').empty();
            $('#cardframe').hide();
            $(document).attr('title', $('body').data('title'))  // <body> stores a 'backup' of the title in a data attribute
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
            if (this.tags.length > 0) {
                url += '/' + this.tags.join(',');
            }
            if (this.hashtags.length > 0) {
                url += '/hash/' + this.hashtags.join(',');
            }
        } else if (this.view = 'map') {
            url += '/' + this.lat + ',' + this.lon + ',' + this.zoom + 'z';
            if (this.tags.length > 0) {
                url += '/' + this.tags.join(',');
            }
            if (this.hashtags.length > 0) {
                url += '/hash/' + this.hashtags.join(',');
            }
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
    ignoreHashChange: false, // used to ignore hash changes triggered by myself
    ignoreMapEvents: false, // ignore next map event
    keepIgnoringMapEvents: false // temporarily ignore map panning and zooming, while processing
};

// parse the hash; the coordinates are used by the google map initialization
state.parseHashStringIntoState();

// start syncing the reference times
//updateNowAndMidnight();

// google maps initialization function (called before jQuery ready!)
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

    if (overrule_style && styles[overrule_style]) {
        // hidden feature:
        map.setOptions({styles:styles[overrule_style]});
        $('#background').css('z-index',10);  // hide controls
    } else {
        map.setOptions({styles:styles['default']});
    }

    // re-center the map if a geo position is available and no coordinates were in the URL
    // and the view is not location or event
    if (!(state.view == 'location' || state.view == 'event') && !state.locationInUrl && navigator.geolocation) {
        // geolocation won't work in newer browser unless https protocol is used!
        browserSupportFlag = true;
        navigator.geolocation.getCurrentPosition(function (position) {
            state.setCenterpoint(position.coords.latitude, position.coords.longitude);
            state.setMapCenterpoint();
            state.generateNewHashString();
        });
    }

    //state.visibleFeatures();

    google.maps.event.addListener(map, 'drag', function() {
        state.panDirty = true;
    });

    google.maps.event.addListener(map, 'zoom_changed', function() {
        state.zoomDirty = true;
    });

    // panning the map or zooming the map
    // (wait for the bounds_changed first)
    google.maps.event.addListenerOnce(map, "bounds_changed", function(){
        state.loadGeoJSON();
        google.maps.event.addListener(map, "idle", function(){
            state.loadGeoJSON();

            if (state.ignoreMapEvents) {
                state.ignoreMapEvents = false;
            } else {
                if (!state.keepIgnoringMapEvents) {
                    if (state.panDirty || state.zoomDirty) {
                        state.keepIgnoringMapEvents = true;
                        if (state.panDirty) {
                            state.getMapCenterpointAndSet();
                            state.panDirty = false;
                        }
                        if (state.zoomDirty) {
                            state.getMapZoomAndSet();
                            state.zoomDirty = false;
                        }
                        state.generateNewHashString();
                        state.keepIgnoringMapEvents = false;
                        state.displayAddEventIcon();
                    }
                }
            }
        });
    });

    // click a marker
    map.data.addListener('click', function(e) {
        state.setViewLocation(e.feature.getProperty('location slug'));
        state.generateNewHashString();
        state.displayIFrame();
        state.visibleFeatures();
        state.displayQrIcon();
        state.displayAddEventIcon();
        state.displayModifyEventIcon();
    });

    state.visibleFeatures();
    state.highlightTimeframeButton();
    state.highlightTagButtons();
    state.highlightHashtagButton();
    state.displayIFrame();
    state.displayQrIcon();
    state.displayAddEventIcon();
    state.displayModifyEventIcon();

    return;
}

// call the google map initialization function (no need to wait for jQuery!)
google.maps.event.addDomListener(window, 'load', initialize);

// jQuery ready
$(document).ready(function() {

    // add event handlers to the action buttons
    $('#timeframe-button').on("click", function() {
        $('#tags-menu,#hash-menu').hide();
        $('#timeframe-menu').toggle();
    });
    $('#tags-button').on("click", function() {
        $('#timeframe-menu,#hash-menu').hide();
        $('#tags-menu').toggle();
    });
    $('#hash-button').on("click", function() {
        $('#timeframe-menu,#tags-menu').hide();
        $('#hash-menu').toggle();
    });

    // add event handlers to the timeframe buttons
    $('#timeframe-menu').on("click", "a", function() {
        $('#timeframe-menu').hide();
        state.setTimeframe(this.id);
        state.visibleFeatures();
        state.generateNewHashString();
        state.highlightTimeframeButton();
        state.displayIFrame();
    });

    $('#tags-menu').on("click", "a", function() {
        $('#tags-menu').hide();
        state.toggleTagInList(this.id);
        state.visibleFeatures();
        state.generateNewHashString();
        state.highlightTagButtons();
        state.displayIFrame();
        state.displayAddEventIcon();
    });

    $('#hash-menu').on("click", "a.search-button", function() {
        $('#hash-menu').hide();
        state.toggleHashtagInList($('#hash-menu input').val());
        state.visibleFeatures();
        state.generateNewHashString();
        state.highlightHashtagButton();
        state.displayIFrame();
        state.displayAddEventIcon();
    });

    $("#hash-menu input").keyup(function(event){
        if(event.keyCode == 13) {
            $("#hash-menu a.search-button").click();
        }
    });

    $('#hash-menu').on("click", "a.search-reset-button", function() {
        $('#hash-menu input').val('');
        $("#hash-menu a.search-button").click();
    });

    History.Adapter.bind(window,'statechange',function() {
        if (state.ignoreHashChange) {
            state.ignoreHashChange = false;
        } else {
            state.parseHashStringIntoState();
            state.visibleFeatures();
            state.setMapCenterpoint();
            state.setMapZoom();
            state.highlightTimeframeButton();
            state.highlightTagButtons();
            state.highlightHashtagButton();
            state.displayIFrame();
            state.displayQrIcon();
            state.displayAddEventIcon();
            state.displayModifyEventIcon();
        }
    });

    return;
});

// handlers for events in the location or event card pane (originally in cards.js)
$(function() {
    $('#cardholder').on('click','.header-close',function() {
        parent.on_click_static_map_in_iframe();
    });
    $('#cardholder').on('click','.header-menu',function() {
        $('#header-menu-items').toggleClass('hidden');
    });
//    $('#cardholder').on('click','#menu-item-website',function() {
//        on_navigation_request_in_iframe($(this).attr('data-website'));
//    });
})

function on_location_known_in_iframe() {
    // called after ajax loading
    // the idea is that the map is centered on this location
    // only if the view is location or event and no location
    // was provided in the URL
    if ((state.view == 'location' || state.view == 'event') && !state.locationInUrl) {
        var latitude = $(".card .header-title").data("latitude");
        var longitude = $(".card .header-title").data("longitude");
        if (latitude && longitude) {
            state.setCenterpoint(latitude, longitude);
            state.setMapCenterpoint();
            state.generateNewHashString();
        }
    }
    return;
}

function on_location_slug_known_in_iframe() {
    // called after ajax for event view, right after loading
    // the idea is that the location slug is used for highlighting the markers
    // because if the event slug is used, other event markers may overlap the
    // highlighted marker
    if (state.view == 'event') {
        var location = $(".card .header-title").data("location-slug");
        state.setLocation(location);
        state.visibleFeatures();
    }
    return;
}

function on_iframe_data_displayed() {
    // called after ajax for event view, right after loading
    $(document).attr('title', $(".card .header-title").text() + " " + $(".card .item-title-card").text());
}

function on_click_static_map_in_iframe() {
    // callable from within iframe
    state.setViewMap();
    state.generateNewHashString();
    state.displayIFrame();
    state.visibleFeatures();
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

function on_click_location_in_iframe(location_slug) {
    // callable from within iframe
    state.setViewLocation(location_slug);
    state.generateNewHashString();
    state.displayIFrame();
    state.displayAddEventIcon();
    state.displayModifyEventIcon();
    return;
}

//function on_navigation_request_in_iframe(url) {
//    // callable from within iframe
//    window.location.href = url;
//}

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

function viewport_tiles(precision) {
    // find the viewport's bottom left and top right coordinates
    var bounds = map.getBounds();
    var ne = bounds.getNorthEast();   // I read that this must be best put
    var sw = bounds.getSouthWest();  // inside the 'idle' event handler
    var box = { top: ne.lat(), bottom: sw.lat(), left: sw.lng(), right: ne.lng()}
    // calculate the list of tiles
    var gaa = geohash_area_area(checkRect(box), precision);
    var tiles = [];
    for (i=0, l=gaa.length; i < l; i++) {
        tiles.push(gaa[i].hash);
    }
    return tiles;
}

function subtract(array1, array2) {
    // return array1, but without elements that are in array2
    var array = [];
    for (var i = 0, l = array1.length; i < l; i++) {
        if (!array2.includes(array1[i]))
            array.push(array1[i]);
    }
    return array;
}

function parent(tiles) {
    // tiles is an array of geohash codes, e.g. "1e55"
    // return a list of (unique) parent geohash codes, e.g. "1e55" becomes "1e5"
    var ps = [];
    for (var i= 0, l = tiles.length; i < l; i++) {
        var p = tiles[i].slice(0,-1);
        if (!ps.includes(p))
            ps.push(p)
    }
    return ps;
}

function complement(parent_tiles, tiles) {
    // parent tiles is an array of geohash codes, e.g. "1e5"
    // tiles is an array of geohash codes, e.g. "1e55"
    //   - of a precision higher than the parent tiles
    //   - all child of one of the parent tiles
    // return a list of geohash codes of the same precision as tiles
    // such that it complements the tiles to cover all parent_tiles
    var geohash_chars = "0123456789bcdefghjkmnpqrstuvwxyz";
    var c = [];
    for (var i=0, l=parent_tiles.length; i < l; i++) {
        for (var j= 0; j < 32; j++) {
            var tile = parent_tiles[i] + geohash_chars[j];
            if (!tiles.includes(tile))
                c.push(tile);
        }
    }
    return c;
}

function geojson_url(tile) {
    // apply sharding for non-localhost
    var sharding_host = window.location.host;
    if (window.location.host.indexOf("localhost") == -1) {
        sharding_host = tile + '.' + sharding_host;
    }
    var url = window.location.protocol + "//" + sharding_host + '/geojson/' + tile;
    // append the ?id= parameter if present in the location, just for debugging on localhost
    // and also append the client timestamp or precision or...
    if (window.location.search) {
        url += window.location.search;
    }
    return url;
}
