// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Highlight active navigation item based on scroll position
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.sidebar a');
    
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (scrollY >= (sectionTop - 200)) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
});

// Add active class styling
const style = document.createElement('style');
style.textContent = `
    .sidebar a.active {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: 500;
    }
`;
document.head.appendChild(style);

// Copy code blocks on click
document.querySelectorAll('.code-block').forEach(block => {
    block.style.cursor = 'pointer';
    block.title = 'Click to copy';
    
    block.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(block.textContent);
            
            // Show feedback
            const originalBg = block.style.backgroundColor;
            block.style.backgroundColor = '#10b981';
            setTimeout(() => {
                block.style.backgroundColor = originalBg;
            }, 200);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    });
});

// Expand/collapse functionality for long content
document.querySelectorAll('.glossary dd').forEach(dd => {
    if (dd.textContent.length > 200) {
        const fullText = dd.textContent;
        const truncated = fullText.substring(0, 200) + '...';
        dd.textContent = truncated;
        
        const expandLink = document.createElement('a');
        expandLink.href = '#';
        expandLink.textContent = ' Show more';
        expandLink.style.color = '#2563eb';
        expandLink.style.fontSize = '0.875rem';
        
        expandLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (dd.textContent.includes('...')) {
                dd.textContent = fullText;
                expandLink.textContent = ' Show less';
            } else {
                dd.textContent = truncated;
                expandLink.textContent = ' Show more';
            }
            dd.appendChild(expandLink);
        });
        
        dd.appendChild(expandLink);
    }
});

// Add loading animation
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease-in';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

// Print functionality
const printButton = document.createElement('button');
printButton.innerHTML = '<i class="fas fa-print"></i> Print';
printButton.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    z-index: 1000;
`;

printButton.addEventListener('click', () => {
    window.print();
});

document.body.appendChild(printButton);

// Table sorting functionality
document.querySelectorAll('.data-table th').forEach((header, index) => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody') || table;
        const rows = Array.from(tbody.querySelectorAll('tr')).slice(1); // Skip header row
        
        const isAscending = header.classList.contains('asc');
        
        rows.sort((a, b) => {
            const aValue = a.cells[index].textContent;
            const bValue = b.cells[index].textContent;
            
            if (!isNaN(aValue) && !isNaN(bValue)) {
                return isAscending ? bValue - aValue : aValue - bValue;
            }
            
            return isAscending ? 
                bValue.localeCompare(aValue) : 
                aValue.localeCompare(bValue);
        });
        
        rows.forEach(row => tbody.appendChild(row));
        
        // Update header classes
        table.querySelectorAll('th').forEach(th => th.classList.remove('asc', 'desc'));
        header.classList.add(isAscending ? 'desc' : 'asc');
    });
});