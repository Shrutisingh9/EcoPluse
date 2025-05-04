// Function to complete an activity
function completeActivity(button, points, id) {
    // Save the completed state in localStorage
    localStorage.setItem(`activity_${id}`, true);

    // Change button color to green and disable it
    button.classList.add('completed');
    button.innerText = `Completed (${points} points)`;
    button.disabled = true;

    // Optionally, you can implement point tracking here, like updating a user's score.
    alert(`You earned ${points} points for completing this activity!`);
}

// Load completed activities from localStorage on page load
window.onload = function() {
    const activities = document.querySelectorAll('.activity-item');

    activities.forEach(activity => {
        const id = activity.getAttribute('data-id');
        const button = activity.querySelector('.complete-btn');

        // Check if activity has been completed before
        if (localStorage.getItem(`activity_${id}`)) {
            // Mark activity as completed
            button.classList.add('completed');
            button.innerText = `Completed`;
            button.disabled = true;
        }
    });
}