var g_dest_album_id = 0;  // where the pictures from an album should go.
var g_access_token = 0;
var g_user_ID = 0;
var g_friend_photos;      // the results of the friend photo fetch
var g_states = [];

function _create_img_elt(id)
{
    var lnk = document.createElement('img');
    lnk.setAttribute('src',"https://graph.facebook.com/" + id + "/picture?access_token=" + g_access_token);
    return lnk;
}


// since chrome doesn't have 'let'
function _closure_maker(f,a)
{
    return function () {
         f(a); 
    };
}

// NOTE: eventually cache state here
var g_states = [];
var g_cur_state;
var g_root;
var g_uploading_root;

// NOTE: don't need a state machine yet. a fair amount of repeated code below could be put in a class though.

// function _AlbumState(get_state_cb)
// {
//     this.name = name;
//     this.active_heading = active_heading;
//     this.get_state = get_state_cb;
    
//     this.prototype.hide = function() 
//     {
//         if(this.active_root)
//             g_root.removeChild(this.active_root);
//     };

//     this.prototype.show = function()
//     {
//         if(this.active_root)
//         {
//             g_root.appendChild(this.active_root);
//         }
//         else
//         {
//             this.get_state();
//         }
//     };
// }


// function _set_active_state(state_name)
// {
//     for(var i = 0; i < g_states.length; ++i)
//     {
//         var state = g_states[i];
//         if(state.name == state_name)
//             state.show();
//         else
//             state.hide();
//     }
// }

function _create_state_root(name, heading_txt)
{
    var node = document.createElement('div');
    node.id = name;

    if(heading_txt)
    {
        var heading = document.createElement('div');
        heading.innerHTML = "<h4>" + heading_txt + "</h4>";
        node.appendChild(heading);
    }
    return node;
}


function albums_init(access_token, uid)
{
    g_root = document.getElementById('root');
    g_uploading_root = document.getElementById('uploading_root');
    g_access_token = access_token;
    g_user_ID = uid;
}

// fb data
// show/hide node
var g_my_albums;

function get_my_albums() 
{
    FB.api('/me/albums', 'get', {
               access_token: g_access_token
           }, function(resp) { my_albums_received(resp); });
    g_my_albums = _create_state_root('my_albums', 'Step 1: Pick an album where you want the photos to be copied to.');
    g_root.appendChild(g_my_albums);
}


function my_albums_received(resp)
{
    for (var i=0, l=resp.data.length; i<l; i++) {
        var album = resp.data[i];
        var album_lnk = _create_img_elt(album.id);
        album_lnk.onclick = _closure_maker(dest_album_selected, album);
        g_my_albums.appendChild(album_lnk);
    }
}

var g_friends;
function dest_album_selected(dest_album)
{
    g_dest_album = dest_album;
    FB.api('/me/friends', 'get', {
               access_token: g_access_token
           }, function(resp) { friends_received(resp); });
    g_friends = _create_state_root('my_friends', 'Step 2: Pick a friend who has pictures you want to grab.');
    g_root.replaceChild(g_friends, g_my_albums);
}



function friends_received(resp)
{
    for(var i=0; i < resp.data.length; i++)
    {
        var friend         = resp.data[i];
        var friend_lnk     = _create_img_elt(friend.id);
        var friend_id      = friend.id;
        friend_lnk.onclick = _closure_maker(get_friend_albums, friend_id);
        g_friends.appendChild(friend_lnk);
    }
}


var g_friend_albums;
function get_friend_albums(friend_id)
{
    FB.api('/'+friend_id+'/albums','get',friend_albums_received);    
    g_friend_albums = _create_state_root('friend_photos', 'click on the album you\'d like to copy photos from');
    g_root.replaceChild(g_friend_albums, g_friends);
}


function friend_albums_received(resp)
{
    for(var i = 0; i < resp.data.length; ++i)
    {
        var album = resp.data[i];
        var album_lnk = _create_img_elt(album.id);
        var album_id = album.id;
        album_lnk.onclick = _closure_maker(friend_album_selected,album_id);
        g_friend_albums.appendChild(album_lnk);        
    }
}


var g_friend_photos;
function friend_album_selected(album_id)
{
    FB.api('/'+album_id+'/photos','get',friend_photos_received);
    g_friend_photos = _create_state_root('friend_photos', 'finally: select photos you\'d like to grab');
    g_root.replaceChild(g_friend_photos, g_friend_albums);
}


function friend_photos_received(resp)
{
    for(var i = 0; i < resp.data.length; ++i)
    {
        var photo = resp.data[i];
        var photo_lnk = _create_img_elt(photo.id);
        photo_lnk.onclick = _closure_maker(friend_photo_selected,resp.data[i]);
        g_friend_photos.appendChild(photo_lnk);
    }
}


function friend_photo_selected(photo)
{
    var node = _create_img_elt(photo.id);
    g_uploading_root.appendChild(node);

    req=new XMLHttpRequest();
    req.open("GET","photo_grabbed?photo_id="+photo.id+"&dst_album="+g_dest_album_id,true);
    req.onreadystatechange = function (aEvt) {
        if (req.readyState == 4) {
            g_uploading_root.removeChild(node);
            if(req.status == 200)
                dump(req.responseText);    
            else
                dump("Error grabbign picture " + photo.id);
        } 
    };
    req.send();
}
