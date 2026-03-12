function toggleEdit(enable){
    const form = document.getElementById('pform');
    const input = form.querySelectorAll('input');
    const select = form.querySelectorAll('select');
    const files = form.querySelectorAll('input[type="file"]');
    const editBtn = document.getElementById('editBtn');
    const saveBtn = document.getElementById('saveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    

    if(enable){
        form.classList.add('edit-mode');
        input.forEach(i => i.removeAttribute('readonly'));
        select.forEach(s => s.removeAttribute('disabled'));
        files.forEach(f => f.removeAttribute('disabled'));
        editBtn.style.display = 'none';
        saveBtn.style.display = 'inline-block';
        cancelBtn.style.display = 'inline-block';
    }
    else{
        window.location.reload();
    }
}