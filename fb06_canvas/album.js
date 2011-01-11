var g_dest_album_id = 0;  // where the pictures from an album should go.

window.get_my_albums = get_my_albums;


function my_albums_received(resp) 
{
    //    if(resp.error) TODO: figure out errors and logging   
    //Log.info('Albums', resp);
    var root = document.getElementById('root');
    var albums_root = document.createElement('div');
    albums_root.id='albums';
    root.appendChild(albums_root);
    
    var pic_album = document.createElement('div')
    albums_root.appendChild(pic_album)
    pic_album.innerHTML = "<h2>Step 1: Pic an album where you want the photos to be copied to.</h2>"
    
    for (var i=0, l=resp.data.length; i<l; i++) {
        var
        album = resp.data[i],
        li = document.createElement('li'),
        a  = document.createElement('a'); 
        a.innerHTML = "<img onclick=function(){ album_selected(album.id); }src='https://graph.facebook.com/" + album.id + "/picture?access_token={{current_user.access_token}}'>";
        a.href = album.link;                                     
        li.appendChild(a);
        albums_root.appendChild(li);
    }
}

function get_my_albums() 
{
    FB.api('/me/albums', 'get', {
               access_token: '{{current_user.access_token}}'
           }, my_albums_received);
};


function friends_received(resp)
{
    var friends_root = document.createElement('div');
    friends_root.id = 'friends_root';
    root.appendChild(friends_root);
    friends_root.innerHTML = '<h2>Step 2: select a friend who has  pictures you\'d like to copy</h2>';
    for(var i=0; i < resp.data.length; i++)
    {
        var friend = resp.data[i];
        var a     = document.createElement('a'); 
        a.innerHTML = "<img onclick=function(){ friend_album_selected("+album.id+"); }src='https://graph.facebook.com/" + album.id + "/picture?access_token={{current_user.access_token}}'>";
        friend_root.appendChild(a);
    }
}

function album_selected(dest_album_id)
{
    g_dest_album_id = dest_album_id;

    var root = document.getElementByID('root');
    var albums_root = document.getElementByID('albums');
    root.removeChild(albums_root);
    
    FB.api('/me/friends', 'get', {
               access_token: '{{current_user.access_token}}'
           }, friend_received); 
}


function friend_albums_received(resp)
{
    var friend_albums_root = document.getElementByID('friend_albums');

    var markup = '';
    if (resp.length > 0) {
        for (var i=0; i<numFriends; i++) {
            
            markup += (
                '<fb:profile-pic size="square" ' +
                    'uid="' + resp[i] + '" ' +
                    'facebook-logo="true"' +
                    '></fb:profile-pic>'
            );
        }
    }
    
    for(var i=0; i < resp.data.length; i++)
    {
        var album = resp.data[i];
        var a     = document.createElement('a'); 
        a.innerHTML = "<img onclick='function(){ friend_album_selected("+album.id+"); }' src='https://graph.facebook.com/" + album.id + "/picture?access_token={{current_user.access_token}}'>";
        friend_albums_root.appendChild(a);
    }
}

function friend_album_selected(album_id)
{
    var root = document.getElementByID('root');
    var albums_root = document.getElementByID('albums');
    root.removeChild(albums_root);    
}