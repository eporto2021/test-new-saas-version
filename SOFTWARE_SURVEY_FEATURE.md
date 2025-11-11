# Software Survey Feature

## Overview
This feature adds a one-time software survey that appears on the home page for new users. The survey allows users to select which software tools they use in their business, helping you better understand their needs and create targeted integrations.

## Features
- ✅ Beautiful, clickable card-based UI showing software tools with icons
- ✅ **Real-time search** to filter through software options
- ✅ **Custom software input** field for tools not listed
- ✅ Automatically disappears after user completes the survey
- ✅ Smooth fade-out animation on submission
- ✅ "Skip for now" option if users want to complete it later
- ✅ Mobile responsive design
- ✅ Admin interface to manage software tools
- ✅ Track which users have completed the survey
- ✅ Search by software name or category
- ✅ Clear search button for easy reset
- ✅ Results counter showing filtered results

## Setup Instructions

### 1. Create Database Migration
Run the following command to create the database migration:

```bash
make migrations
```

Or directly with Docker:
```bash
docker compose run --rm web python manage.py makemigrations
```

### 2. Apply Migration
Run the migration to update your database:

```bash
make migrate
```

Or:
```bash
docker compose run --rm web python manage.py migrate
```

### 3. Populate Software Tools
Populate the database with initial software tools:

```bash
make manage ARGS='populate_software'
```

Or:
```bash
docker compose run --rm web python manage.py populate_software
```

This will create entries for:
- Optimo Route
- Xero
- Google Ads
- Excel
- WhatsApp
- Connect Teams
- Slack
- QuickBooks
- Salesforce
- HubSpot
- Mailchimp
- Shopify
- Google Sheets
- Asana
- Trello
- Zoom
- Google Analytics
- Stripe

## Usage

### For Users
1. When a user logs in for the first time, they'll see the software survey section
2. **Use the search box** to quickly find specific software (e.g., type "Excel" or "accounting")
3. Click on any software tools they use (cards will highlight when selected)
4. **Add custom software** in the "Other Software Not Listed" field if their tools aren't shown
5. Click "Submit" to save their selections
6. The survey disappears and won't show again
7. Alternatively, they can click "Skip for now" to skip the survey (also marks it as completed)

### Search Features
- **Real-time filtering**: As you type, software cards are filtered instantly
- **Search by name or category**: Search works for both software names (e.g., "Xero") and categories (e.g., "accounting")
- **Clear button**: Click the X button to clear your search
- **Results counter**: Shows how many results match your search
- **No results message**: If nothing matches, you're prompted to add it as custom software

### For Admins

#### Managing Software Tools
1. Go to Django Admin: `/admin/`
2. Navigate to "Software" under the Users section
3. Add, edit, or remove software tools
4. Configure:
   - **Name**: Display name of the software
   - **Icon**: Font Awesome icon class (e.g., `fa-route`, `fa-calculator`)
   - **Category**: Grouping category (e.g., "Route Planning", "Accounting")
   - **Order**: Display order (lower numbers appear first)
   - **Is Active**: Toggle to show/hide the tool in the survey

#### Viewing User Software Selections
1. Go to Django Admin: `/admin/`
2. Navigate to "Users" → "Custom users"
3. Click on a user to see:
   - **Selected software tools** (from the predefined list)
   - **Custom software** (tools they manually entered)
4. Filter users by "completed_software_survey" to see who has/hasn't completed it

#### Understanding Custom Software Entries
- Users can enter multiple custom software names separated by commas
- This text is stored in the `custom_software` field
- Review these entries to identify popular software that should be added to the main list
- Use this data to improve your software catalog over time

## Database Models

### Software Model
```python
- name: CharField (unique)
- icon: CharField (Font Awesome class)
- category: CharField
- order: IntegerField
- is_active: BooleanField
```

### CustomUser Additions
```python
- software_tools: ManyToManyField(Software)
- custom_software: TextField (for software not in predefined list)
- completed_software_survey: BooleanField
```

## Customization

### Adding More Software Tools
You can add more software tools via:

1. **Django Admin** (recommended for non-developers)
2. **Management Command**: Edit `apps/users/management/commands/populate_software.py`
3. **Directly in code**: Create Software objects

### Changing the UI
The survey styling is in `templates/web/app_home.html` within a `<style>` tag. Key classes:
- `.software-grid`: Grid layout
- `.software-card`: Individual tool card
- `.software-card-content`: Card styling
- `.software-icon`: Icon styling

### Font Awesome Icons
Find icons at: https://fontawesome.com/icons
Use the class name like: `fa-route`, `fa-whatsapp`, `fa-calculator`

## API Endpoints

### Submit Survey
- **URL**: `/submit-software-survey/`
- **Method**: POST
- **Auth**: Required (login_required)
- **Parameters**: 
  - `software[]` (array of software IDs from predefined list)
  - `custom_software` (optional text field for unlisted software)
- **Response**: Redirect to home page with success message

## Future Enhancements
- Allow users to update their software selections later
- Add a "Manage Software" page for users
- Send recommendations based on selected software
- Analytics dashboard showing most popular software (both predefined and custom)
- Integration suggestions based on user's software stack
- Auto-suggest feature based on custom software entries
- Ability to convert popular custom entries into predefined options
- Export user software data for analysis

## Troubleshooting

### Survey not showing
- Check that `completed_software_survey` is `False` for the user
- Verify there are active software tools in the database
- Check that the user is logged in

### Icons not displaying
- Ensure Font Awesome is loaded in your base template
- Verify icon class names are correct (e.g., `fa-route` not just `route`)
- Check that Font Awesome version supports the icons you're using

### Search not working
- Check browser console for JavaScript errors
- Verify all software cards have `data-name` and `data-category` attributes
- Ensure the search input has the correct ID (`software-search`)

### Custom software not saving
- Check that the textarea has `name="custom_software"`
- Verify the view is correctly processing the POST data
- Check the database field allows TextField (long text)

### Styling issues
- Check browser console for CSS errors
- Verify Bootstrap classes are available
- Test responsive design on different screen sizes

