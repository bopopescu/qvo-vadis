var geocoder;
var map;
var layer;
var layer2;
var marker;

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
// initialise the google maps objects, and add listeners
function gmaps_init() {

    // center of the universe TODO make this a configurable default
    var latlng = new google.maps.LatLng(51.2205424,4.4224811);

    var options = {
        zoom: 17,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        mapTypeControl: false,
        panControl: false,
        zoomControl: true,
//        zoomControlOptions: {
//          style: google.maps.ZoomControlStyle.SMALL,
//          position: google.maps.ControlPosition.RIGHT_BOTTOM
//        },
        scaleControl: false,
        streetViewControl: false
    };

    // center the map if a geo position is available and no coordinates were in the URL
    if (event_default || location_default || coordinates_default) {
        var latLng = new google.maps.LatLng(original_event['latitude'], original_event['longitude']);
        options.center = latLng;
        if (coordinates_default) {
            options.zoom = parseInt(original_event['zoom']);
        }
    } else if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var latLng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
            options.center = latLng;
        });
    }
    // create our map object
    var mapDiv = document.getElementById("gmaps-canvas");
    map = new google.maps.Map(mapDiv, options);

    // load geojson containing current locations
    var simple_url = window.location.protocol + "//" + window.location.host + "/geojsonsimple";
    if (location.search) {
        simple_url += location.search;
    }
    map.data.loadGeoJson(simple_url);

    // load geojson containing predefined locations
    var locations_url = window.location.protocol + "//" + window.location.host + "/geojsonlocations";
    if (location.search) {
        locations_url += location.search;
    }
    map.data.loadGeoJson(locations_url);

    // style the markers
    var set_style = function(feature) {
        // check if the location should be highlighted
        if (feature.getProperty('predefined') == "no")
            var url = window.location.protocol + "//" + window.location.host + '/images/map-marker-small-red.png';
        else if (feature.getProperty('predefined') == "yes")
            var url = window.location.protocol + "//" + window.location.host + '/images/map-marker-small-green.png';
        return {
            icon: {
                url: url,
                scaledSize: new google.maps.Size(24, 24),
                anchor: new google.maps.Point(12, 12),
                cursor: "pointer"
            }
        };
    };
    map.data.setStyle(set_style);

    // the geocoder object allows us to do latlng lookup based on address
    geocoder = new google.maps.Geocoder();

    // the placesservice object allows us to fetch data from a place
    placesservice = new google.maps.places.PlacesService(map);

    // the marker shows us the position of the latest address
    marker = new google.maps.Marker({
        map: map,
        draggable: true
    });

    // marker.setPosition(latLng); // is the marker automatically centered on the map?

    // event triggered when marker is dragged and dropped
    google.maps.event.addListener(marker, 'dragend', function() {
        geocode_lookup('latLng', marker.getPosition());
    });

    // event triggered when map is clicked
    google.maps.event.addListener(map, 'click', function(event) {
        marker.setPosition(event.latLng);
        if (event.placeId) {
            event.stop()  // don't show the balloon
            placesservice.getDetails({placeId: event.placeId}, function(place, status) {
                update_ui({
                    address: place.formatted_address,
                    postal_code: get_postal_code(place),
                    name: place.name,
                    location: event.latLng
                });
                return;
            });
        } else {
            geocode_lookup('latLng', event.latLng);
        }
    });

    $('#gmaps-error').hide();

    map.data.addListener('click', function(e) {
        var latlng = e.feature.getGeometry().get();
        if (e.feature.getProperty('predefined') == "no") {
            // clicking on a location that's in the database of events
            var location_slug = e.feature.getProperty('location_slug');
            // query for the event attributes on the server
            var url = window.location.protocol + "//" + window.location.host + "/geojsonlocation/" + location_slug;
            if (location.search) {
                url += location.search;
            }
            $.getJSON(url, function(data) {
                // fill in the fields on the left side
                var properties = data['features'][0]['properties'];
                var address = properties['address'];
                var name = properties['location_name'];
                var postal_code = properties['postal_code'];
                update_ui({
                    address: address,
                    postal_code: postal_code,
                    name: name,
                    location: latlng
                });
                marker.setPosition(latlng);
            });
        } else {
            // clicking on a location that's in the database of predefined locations
            var name = e.feature.getProperty('name');
            geocoder.geocode({latLng: latlng}, function(results, status) {
                if (status == google.maps.GeocoderStatus.OK) {
                    // Google geocoding has succeeded!
                    if (results[0]) {
                        // Always update the UI elements with new location data
                        update_ui({
                            address: '',
                            postal_code: get_postal_code(results[0]),
                            name: name,
                            location: latlng
                        });
                        marker.setPosition(latlng);
                        return;
                    }
                }
                // Geocoder status ok but no results!? or status not ok
                update_ui({
                    address: '',
                    postal_code: '',
                    name: name,
                    location: latlng
                });
                marker.setPosition(latlng);
                return;
            });
        }
    })
}

// move the marker to a new position, and center the map on it
function update_map(geometry) {
    map.fitBounds(geometry.viewport)
    marker.setPosition(geometry.location)
}

function location_visualization(data) {
    var address = data.address;
    var name = data.name;
    var latLng = data.location;
    var postal_code = data.postal_code;
    var location = name;
    if (address) {
        if (name) {
            location += ', ';
        }
        location += address;
        $('#edit-location').show();
    } else {
        if (name) {
            location += ' ';
        }
        location += '(' + postal_code + ')';
        $('#edit-location').show();
    }
    $('#location').html(location);
}
// fill in the UI elements with new position data
function update_ui(data) {
    var address = data.address;
    var name = data.name;
    var latLng = data.location;
    var postal_code = data.postal_code;
    if (!address && !name) {
        $('#edit-location').hide();
    }
    $('#address').autocomplete("close");
    $('#address').val(address);
    $('#address').removeClass('error');
    $('#location-name').val(name);
    $('#location-name').removeClass('error');
    $('#gmaps-output-latitude').html(latLng.lat());
    $('#gmaps-output-longitude').html(latLng.lng());
    $('#gmaps-output-postal-code').html(postal_code);
    location_visualization(data);
}

// Query the Google geocode object
//
// type: 'address' for search by address
//       'latLng'  for search by latLng (reverse lookup)
//
// value: search query
//
// update: should we update the map (center map and position marker)?
function geocode_lookup(type, value, update) {
    // default value: update = false
    update = typeof update !== 'undefined' ? update : false;

    request = {};
    request[type] = value;

    geocoder.geocode(request, function(results, status) {
        $('#gmaps-error').html('');
        $('#gmaps-error').hide();
        if (status == google.maps.GeocoderStatus.OK) {
            // Google geocoding has succeeded!
            if (results[0]) {
                // Always update the UI elements with new location data
                update_ui({
                    address: results[0].formatted_address,
                    postal_code: get_postal_code(results[0]),
                    name: '', 
                    location: results[0].geometry.location
                });

                // Only update the map (position marker and center map) if requested
                if (update) {
                    update_map(results[0].geometry);
                }
            }
            else {
                // Geocoder status ok but no results!?
                $('#gmaps-error').html("Sorry, something went wrong. Try again!");
                $('#gmaps-error').show();
            }
        }
        else {
            // Google Geocoding has failed. Two common reasons:
            //   * Address not recognised (e.g. search for 'zxxzcxczxcx')
            //   * Location doesn't map to address (e.g. click in middle of Atlantic)

            if (type == 'address') {
                // User has typed in an address which we can't geocode to a location
                $('#gmaps-error').html("Sorry! We couldn't find " + value + ". Try a different search term, or click the map.");
                $('#gmaps-error').show();
            }
            else {
                // User has clicked or dragged marker to somewhere that Google can't do a reverse lookup for
                // In this case we display a warning, clear the address box, but fill in LatLng
                $('#gmaps-error').html("Woah... that's pretty remote! You're going to have to manually enter a place name.");
                $('#gmaps-error').show();
                update_ui({
                    address: '',
                    postal_code: '',
                    name: '',
                    location: value
                })
            }
        };
    });
}

// initialise the jqueryUI autocomplete element
function autocomplete_init() {
    $("#address").autocomplete({

        // source is the list of input options shown in the autocomplete dropdown.
        // see documentation: http://jqueryui.com/demos/autocomplete/
        source: function(request, response) {

            // the geocode method takes an address or LatLng to search for
            // and a callback function which should process the results into
            // a format accepted by jqueryUI autocomplete
            geocoder.geocode({
                'address': request.term
            }, function(results, status) {
                response($.map(results, function(item) {
                    return {
                        label: item.formatted_address, // appears in dropdown box
                        value: item.formatted_address, // inserted into input element when selected
                        geocode: item // all geocode data: used in select callback event
                    };
                }));
            });
        },

        // event triggered when drop-down option selected
        select: function(event, ui) {
            update_ui({
                address: ui.item.value,
                postal_code: get_postal_code(ui.item.geocode),
                name: '',
                location: ui.item.geocode.geometry.location
            });
            update_map(ui.item.geocode.geometry);
        }
    });

    // triggered when user presses a key in the address box
    $("#address").bind('keydown', function(event) {
        if (event.keyCode == 13) {
            geocode_lookup('address', $('#address').val(), true);

            // ensures dropdown disappears when enter is pressed
            $('#address').autocomplete("disable");
        }
        else {
            // re-enable if previously disabled above
            $('#address').autocomplete("enable");
        }
    });

} // autocomplete_init

function get_postal_code(res) {
    var zip = "";
	for (var i = 0; i < res.address_components.length; i++) {
		if (res.address_components[i].types[0] == "postal_code") {
			zip = res.address_components[i].short_name;
		}
	}
	return zip;
}

function pad(n) { return ("0" + n).slice(-2); }

function newDate(dateTimeString) {
    // custom function that parses a date formatted like %Y-%m-%d %H:%M:%S
    var dateTimeArray = dateTimeString.split(" ");
    var dateArray = dateTimeArray[0].split('-');
    var timeArray = dateTimeArray[1].split(':');
    var date = new Date(dateArray[0],dateArray[1]-1,dateArray[2],timeArray[0],timeArray[1],timeArray[2]);
    return date;
}

function initialize_data() {
    // called from $(), *after* datepicker is initialized
    if (event_default) {
        var start_date = newDate(original_event['start']);
        var end_date = newDate(original_event['end']);
        var today = new Date();
        if (start_date < today) {
            var new_start_date = today;
            new_start_date.setHours(start_date.getHours());
            new_start_date.setMinutes(start_date.getMinutes());
            new_start_date.setTime(new_start_date.getTime() + 86400000); /* plus one day */
            var duration = end_date - start_date;
            start_date = new_start_date;
            end_date.setTime(new_start_date.getTime() + duration);
        }
        $('#start-date').datepicker('setDate', start_date);
        $('#start-hour').timepicker('setTime', start_date);
        $('#end-date').datepicker('setDate', end_date);
        $('#end-hour').timepicker('setTime', end_date);
        if (original_event['calendar rule']) {
            $('#rrule').val(original_event['calendar rule']);
            $('#repeating').prop('checked', true);
            $('a[name=riedit]').trigger('click');
        }
        $('#event-name').val(original_event['event name']);
        $('#description').val(original_event['description']);
        $('#contact').val(original_event['contact']);
        $('#website').val(original_event['website']);
        if (original_event['registration required'] == 'true') {
            $('#registration-required').prop('checked', true);
        }
        $('#owner').val(original_event['owner']);
    }
    if (event_default || location_default) {
        $('#location-name').val(original_event['location name']);
        $('#address').val(original_event['address']);
        $('#gmaps-output-postal-code').text(original_event['postal code']);
        $('#gmaps-output-latitude').text(original_event['latitude']);
        $('#gmaps-output-longitude').text(original_event['longitude']);
        // initializing map position cannot be done here... find 'setCenter'
        $('#location-details').val(original_event['location details']);
    }
//    if (coordinates_default) {
        // initializing map position cannot be done here... find 'setCenter'
//    }
    if (event_default || tags_default) {
        $('.tag').each(function() {
            var tag = $(this).attr('id');
            if (original_event['tags'].includes(tag)) {
                $(this).prop('checked', true);
            }
        });
    }
    if (hashtags_default) {
        var description = [];
        $.each(original_event['hashtags'].split(','),function(index,value) {
            description.push('#' + value.slice(1,-1)); // remove the #-es
        });
        $('#description').val(description.join(' '));
    }
}

$(document).ready(function() {
    var duration = 3600000; /* one hour */
    $("#rrule").recurrenceinput({lang:language, startField: "start-date"});
    $.datepicker.setDefaults( $.datepicker.regional[language] );  // download more locales from http://jquery-ui.googlecode.com/svn/tags/latest/ui/i18n/
    $(".date").datepicker();
    $(".time").timepicker({
        'timeFormat': 'H:i'
        // 'disableTimeRanges': [ ['24:00', '24:01'] ]
    });
    var start = new Date();
    var end = new Date();
    end.setTime(start.getTime() + duration);
    $("#start-date").datepicker("setDate", start);
    $("#end-date").datepicker("setDate", end);
    $("#start-hour").timepicker("setTime", start);
    $("#end-hour").timepicker("setTime", end);
    $("#start-date,#start-hour").change(function() {
        var start = $("#start-hour").timepicker("getTime",$("#start-date").datepicker("getDate"));
        var end = new Date();
        end.setTime(start.getTime() + duration);
        $("#end-date").datepicker("setDate", end);
        $("#end-hour").timepicker("setTime", end);
    });
    $("#end-date,#end-hour").change(function() {
        var start = $("#start-hour").timepicker("getTime",$("#start-date").datepicker("getDate"));
        var end = $("#end-hour").timepicker("getTime",$("#end-date").datepicker("getDate"));
        duration = end - start;
    });
    initialize_data();
    if ($('#gmaps-canvas').length) {
        gmaps_init();
        autocomplete_init();
    }
    $('#location-ok').click(function() {
        $('#location-modal').hide();
        location_visualization({
            address: $('#address').val(),
            name: $('#location-name').val(),
            location: new google.maps.LatLng($('#gmaps-output-latitude').html(),$('#gmaps-output-longitude').html()),
            postal_code: $('#gmaps-output-postal-code').html()
        })
    });
    $('#edit-location').click(function() {
        $('#location-modal').show();
    });

    // functions and event handling for the editing form in general, not limited to gmaps

    $('form').submit(function() {
        return false;
    });
    $('#main-save').click(function() {
        $('.message-text').hide();
        // read form data into event object
        var now = new Date();
        now.setHours(0);
        now.setMinutes(0);
        now.setSeconds(0);
        now.setMilliseconds(0);
        var event = {};
        event['event slug'] = '';
        var start_date = $("#start-date").datepicker("getDate");
        if (start_date < now) {
            $('#information-missing').show();
            $('#start-date-past').show();
            $('#start-date').addClass('error');
        }
        var start_time_string = $('#start-hour').val() + ":00";
        if (start_time_string == "24:00:00") {
            start_date.setDate(start_date.getDate() + 1);
            start_time_string = "00:00:00";
        }
        var start_date_string = $.datepicker.formatDate("yy-mm-dd", start_date);
        var start_string = start_date_string + " " + start_time_string;
        var start_string_for_parsing = start_date_string + "T" + start_time_string;
        if (isNaN(Date.parse(start_string_for_parsing))) {
            $('#information-missing').show();
            $('#start-hour-wrong').show();
            $('#start-hour').addClass('error');
        }
        event['start'] = start_string;
        var end_date = $("#end-date").datepicker("getDate");
        if (end_date < start_date) {
            $('#information-missing').show();
            $('#end-date-before-start-date').show();
            $('#end-date').addClass('error');
        }
        var end_time_string = $('#end-hour').val() + ":00";
        if (end_time_string == "24:00:00") {
            end_date.setDate(end_date.getDate() + 1);
            end_time_string = "00:00:00";
        }
        var end_date_string = $.datepicker.formatDate("yy-mm-dd", end_date);
        var end_string = end_date_string + " " + end_time_string;
        var end_string_for_parsing = end_date_string + "T" + end_time_string;
        if (isNaN(Date.parse(end_string_for_parsing))) {
            $('#information-missing').show();
            $('#end-hour-wrong').show();
            $('#end-hour').addClass('error');
        }
        if (end_string < start_string) {
            $('#information-missing').show();
            $('#end-hour-before-start-hour').show();
            $('#end-hour').addClass('error');
        }
        event['end'] = end_string;
        event['calendar rule'] = $('#rrule').val();
        event['event name'] = $('#event-name').val();
        if (!event['event name']) {
            $('#information-missing').show();
            $('#no-event-name').show();
            $('#event-name').addClass('error');
        }
        event['description'] = $('#description').val();
        event['contact'] = $('#contact').val();
        event['website'] = $('#website').val();
        event['registration required'] = $('#registration-required').is(':checked') ? 'true' : 'false';
        event['owner'] = $('#owner').val();
        event['address'] = $('#address').val();
        event['location name'] = $('#location-name').val();
        if (!event['location name'] && !event['address']) {
            $('#information-missing').show();
            $('#location-name-nor-address').show();
            $('#address').addClass('error');
            $('#location-modal').show();
        }
        event['postal code'] = $('#gmaps-output-postal-code').text();
        event['latitude'] = $('#gmaps-output-latitude').text().replace(',','.');
        event['longitude'] = $('#gmaps-output-longitude').text().replace(',','.');  // I've seen comma in the table, no idea how it got there
        if (!event['latitude']) {
            $('#information-missing').show();
            $('#no-marker').show();
            $('#address').addClass('error');
            $('#location-modal').show();
        }
        event['location details'] = $('#location-details').val();
        var tags = [];
        $('.tag').each(function() {
            if ( $(this).is(':checked') ) {
                tags.push($(this).attr('id'));
            }
        });
        event['tags'] = tags.join();
        if ($('.error').length) {
            // there are errors
            return false;
        }
        var data = JSON.stringify(event);
        if (edit_mode == 'new') {
            var url = "/submit/new";
        } else {
            var url = "/submit/update/" + original_event['event slug'];
        }
        if (location.search) {
            url += location.search;
        }
        $('input,select,textarea').prop('disabled', true);
        $('#spinner').show();
        $.post(url, {data: data})
            .done(function(data) {
                var url = '/';
                url += 'all/event/';
                url += data;
                if (location.search) {
                    url += location.search;
                }
                location.href = url;
            });
        return false;
    });
    $('#main-cancel').click(function() {
        return false;
    });
    $('#main-discard').click(function() {
        return false;
    });
    $('#main-help').click(function() {
        return false;
    });
    $("div.section:not('.modal') input").keypress(function(event) {
        if (event.which == 13) {  // enter key
            event.preventDefault();
            $("#main-save").click();
        }
    });
    $("div.section.modal input").keypress(function(event) {
        if (event.which == 13) {  // enter key
            event.preventDefault();
        }
    });
    // triggered when user selects an input field
    $("input,textarea,select").bind('focus', function() {
        $(this).removeClass('error');
    });
});
