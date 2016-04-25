// copied to map.js
$(function() {
    $('.header-close').on('click',function() {
        parent.on_click_static_map_in_iframe();
    });
    $('.header-menu').on('click',function() {
        $('#header-menu-items').toggleClass('hidden');
    });
    $('#menu-item-website').on('click',function() {
        parent.on_navigation_request_in_iframe($(this).attr('data-website'));
    });
})
