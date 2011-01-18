var g_dest_album;  // where the pictures from an album should go.
var g_access_token = 0;
var g_user_ID = 0;
var g_friend_photos;      // the results of the friend photo fetch
var g_states = [];

function _create_img_elt(id, img_name)
{
    var root = document.createElement('div');
    var lnk = document.createElement('img');
    root.id = id;
    lnk.setAttribute('src',"https://graph.facebook.com/" + id + "/picture?access_token=" + g_access_token);
    lnk.alt = img_name;

    root.appendChild(lnk);
    // if(img_name)
    // {
    //     var name = document.createElement('div');
    //     name.innerHTML = img_name;
    //     root.appendChild(name);
    // }
    root.style = "hover{color:#ff0080;}";
    return root;
}


// since chrome doesn't have 'let'
function _closure_maker(f,a)
{
    return function () {
         f(a); 
    };
}

function _elt_remove_all_children(elt)
{
    if(elt && elt.hasChildNodes())
    {
        while(elt.childNodes.length > 0)
            elt.removeChild(elt.firstChild);
    }
}

function _elt_replace_children_with(elt,new_child)
{
    _elt_remove_all_children(elt);
    elt.appendChild(new_child);
}

// NOTE: eventually cache state here
var g_states = [];
var g_cur_state;
var g_root;

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
    g_access_token = access_token;
    g_user_ID = uid;
}

// fb data
// show/hide node
var g_my_albums;
var g_my_albums_resp;
function get_my_albums() 
{
    if(!g_my_albums_resp)
    {
        FB.api('/me/albums', 'get', {
                   access_token: g_access_token
               }, function(resp) { my_albums_received(resp); });
        g_my_albums = _create_state_root('my_albums', 'Step 1: Pick an album where you want the photos to be copied to.');
        g_root.appendChild(g_my_albums);
    }
    else
    {
        my_albums_received(g_my_albums_resp);
    }
}



function my_albums_received(resp)
{
    g_my_albums_resp = resp;
    for (var i=0, l=resp.data.length; i<l; i++) {
        var album = resp.data[i];
        var album_lnk = _create_img_elt(album.id, album.name);
        album_lnk.onclick = _closure_maker(dest_album_selected, album);
        album.title = album.name
        g_my_albums.appendChild(album_lnk);
    }
}


function choose_step1()
{
    _elt_remove_all_children(g_my_albums);
    _elt_remove_all_children(g_friends);
    _elt_remove_all_children(g_friend_albums);
    _elt_remove_all_children(g_friend_photos);
    my_albums_received(g_my_albums_resp);
}

var g_friends;
function dest_album_selected(dest_album)
{
    g_dest_album = dest_album;
    var dst_album_node = document.createTextNode('Step 1: putting photos in album: "' + dest_album.name + '"');
//    dst_album_node.onclick = choose_step1();

    _elt_replace_children_with(g_my_albums,dst_album_node);

    FB.api('/me/friends', 'get', {
               access_token: g_access_token
           }, function(resp) { friends_received(resp); });
    g_friends = _create_state_root('my_friends', 'Step 2: Pick a friend who has pictures you want to grab.');
    g_root.appendChild(g_friends);
}



function friends_received(resp)
{
    for(var i=0; i < resp.data.length; i++)
    {
        var friend         = resp.data[i];
        var friend_lnk     = _create_img_elt(friend.id);
        var friend_id      = friend.id;
        friend_lnk.onclick = _closure_maker(get_friend_albums, friend);
        g_friends.appendChild(friend_lnk);
    }
}


var g_friend_albums;
function get_friend_albums(friend)
{
    _elt_replace_children_with(g_friends,document.createTextNode("Step 2: grabbing from friend " + friend.name))
    FB.api('/'+friend.id+'/albums','get',friend_albums_received);    
    g_friend_albums = _create_state_root('friend_photos', 'Step 3: Click on the album you\'d like to copy photos from.');
    g_root.appendChild(g_friend_albums);
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
    g_friend_photos = _create_state_root('friend_photos', 'Finally: select photos you\'d like to grab by clicking on them:');
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
    var access_token = FB.getSession().access_token;
    var photo_elt = document.getElementById(photo.id);
    var grab_elt = document.createTextNode("grabbing photo " + photo.id);
    
    _elt_replace_children_with(photo_elt, grab_elt);

    req=new XMLHttpRequest();
    req.open("GET","photo_grabbed?photo_id="+photo.id+"&dst_album="+g_dest_album.id+"&access_token="+FB.getSession().access_token,true);
    req.onreadystatechange = function (aEvt) {
        if (req.readyState == 4) {
            if(req.status == 200)
            {
                grab_elt.textContent = photo.id + " uploaded";
            }
            else
                alert("Error grabbing picture " + photo.name + '(' + photo.id + ')');
        } 
    };
    req.send();
}
