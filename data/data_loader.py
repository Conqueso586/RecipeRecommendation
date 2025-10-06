from models.models import db, Recipe

def init_sample_data():
    """Initialize the database with sample recipes."""
    
    if Recipe.query.count() > 0:
        print("Sample data already exists. Skipping initialization.")
        return

    sample_recipes = [
        {
            'name': 'Classic Chicken Stir Fry',
            'ingredients': ['chicken breast', 'bell peppers', 'onion', 'garlic', 'soy sauce', 'vegetable oil', 'rice', 'ginger'],
            'instructions': '1. Cut chicken into strips and season with salt and pepper.\n2. Heat oil in a large wok or skillet over high heat.\n3. Cook chicken until golden brown and cooked through, about 5-6 minutes.\n4. Add vegetables and stir fry for 3-4 minutes until crisp-tender.\n5. Add garlic and ginger, cook for 30 seconds.\n6. Add soy sauce and toss to combine.\n7. Serve immediately over steamed rice.',
            'prep_time': 15,
            'cook_time': 10,
            'servings': 4,
            'cuisine_type': 'Asian',
            'difficulty': 'Easy'
        },
        {
            'name': 'Creamy Pasta Carbonara',
            'ingredients': ['pasta', 'bacon', 'eggs', 'parmesan cheese', 'black pepper', 'garlic', 'heavy cream'],
            'instructions': '1. Cook pasta according to package directions until al dente.\n2. While pasta cooks, fry bacon until crispy and golden.\n3. In a bowl, whisk together eggs, grated parmesan, and black pepper.\n4. Add minced garlic to bacon and cook for 1 minute.\n5. Drain pasta and add to bacon pan.\n6. Remove from heat and quickly toss with egg mixture.\n7. Add cream if needed for consistency.\n8. Serve immediately with extra parmesan.',
            'prep_time': 10,
            'cook_time': 15,
            'servings': 4,
            'cuisine_type': 'Italian',
            'difficulty': 'Medium'
        },
        {
            'name': 'Vegetarian Black Bean Tacos',
            'ingredients': ['black beans', 'corn tortillas', 'avocado', 'tomatoes', 'red onion', 'lime', 'cilantro', 'cheese', 'lettuce'],
            'instructions': '1. Rinse and drain black beans, then heat with cumin and chili powder.\n2. Warm tortillas in a dry skillet or microwave.\n3. Dice tomatoes and red onion finely.\n4. Slice avocado and squeeze with lime juice.\n5. Shred lettuce and grate cheese.\n6. Assemble tacos with beans as base, then add vegetables.\n7. Top with cilantro and serve with lime wedges.\n8. Serve immediately while tortillas are warm.',
            'prep_time': 15,
            'cook_time': 5,
            'servings': 4,
            'cuisine_type': 'Mexican',
            'difficulty': 'Easy'
        },
        {
            'name': 'Beef and Mushroom Risotto',
            'ingredients': ['arborio rice', 'beef broth', 'mushrooms', 'ground beef', 'onion', 'white wine', 'parmesan cheese', 'butter'],
            'instructions': '1. Heat beef broth in a separate pot and keep warm.\n2. Brown ground beef in a large pan and set aside.\n3. In the same pan, sauté diced onions until translucent.\n4. Add sliced mushrooms and cook until golden.\n5. Add arborio rice and toast for 2 minutes.\n6. Pour in wine and stir until absorbed.\n7. Add warm broth one ladle at a time, stirring constantly.\n8. Continue until rice is creamy, about 18-20 minutes.\n9. Stir in cooked beef, butter, and parmesan.\n10. Season and serve immediately.',
            'prep_time': 20,
            'cook_time': 30,
            'servings': 4,
            'cuisine_type': 'Italian',
            'difficulty': 'Hard'
        },
        {
            'name': 'Mediterranean Greek Salad',
            'ingredients': ['cucumber', 'tomatoes', 'red onion', 'feta cheese', 'kalamata olives', 'olive oil', 'lemon juice', 'oregano'],
            'instructions': '1. Wash and chop cucumber into chunks.\n2. Cut tomatoes into wedges.\n3. Slice red onion into thin rings.\n4. Crumble feta cheese into bite-sized pieces.\n5. In a large bowl, combine cucumber, tomatoes, and onion.\n6. Add olives and feta cheese.\n7. In a small bowl, whisk olive oil, lemon juice, and oregano.\n8. Drizzle dressing over salad and toss gently.\n9. Let sit for 10 minutes before serving to allow flavors to meld.',
            'prep_time': 15,
            'cook_time': 0,
            'servings': 4,
            'cuisine_type': 'Mediterranean',
            'difficulty': 'Easy'
        },
        {
            'name': 'Classic Chocolate Chip Cookies',
            'ingredients': ['all-purpose flour', 'butter', 'brown sugar', 'white sugar', 'eggs', 'vanilla extract', 'baking soda', 'salt', 'chocolate chips'],
            'instructions': '1. Preheat oven to 375°F (190°C).\n2. In a large bowl, cream together softened butter and both sugars.\n3. Beat in eggs one at a time, then add vanilla.\n4. In separate bowl, whisk flour, baking soda, and salt.\n5. Gradually mix dry ingredients into wet ingredients.\n6. Fold in chocolate chips.\n7. Drop rounded tablespoons of dough onto ungreased baking sheets.\n8. Bake for 9-11 minutes until golden brown.\n9. Cool on baking sheet for 5 minutes before transferring.\n10. Store in airtight container.',
            'prep_time': 20,
            'cook_time': 11,
            'servings': 24,
            'cuisine_type': 'American',
            'difficulty': 'Easy'
        },
        {
            'name': 'Thai Green Curry',
            'ingredients': ['chicken thighs', 'coconut milk', 'green curry paste', 'thai basil', 'bell peppers', 'bamboo shoots', 'fish sauce', 'brown sugar', 'lime'],
            'instructions': '1. Cut chicken into bite-sized pieces.\n2. Heat 1/2 cup coconut milk in a large pan over medium heat.\n3. Add green curry paste and cook until fragrant.\n4. Add chicken and cook until no longer pink.\n5. Pour in remaining coconut milk and bring to simmer.\n6. Add bell peppers and bamboo shoots.\n7. Season with fish sauce and brown sugar.\n8. Simmer for 10-15 minutes until chicken is cooked through.\n9. Stir in thai basil leaves.\n10. Serve with rice and lime wedges.',
            'prep_time': 15,
            'cook_time': 20,
            'servings': 4,
            'cuisine_type': 'Thai',
            'difficulty': 'Medium'
        },
        {
            'name': 'Caprese Stuffed Chicken',
            'ingredients': ['chicken breasts', 'mozzarella cheese', 'cherry tomatoes', 'fresh basil', 'balsamic glaze', 'olive oil', 'garlic', 'salt', 'pepper'],
            'instructions': '1. Preheat oven to 400°F (200°C).\n2. Cut a pocket in each chicken breast, being careful not to cut through.\n3. Season chicken inside and out with salt and pepper.\n4. Stuff each breast with mozzarella, halved cherry tomatoes, and basil.\n5. Secure with toothpicks if needed.\n6. Heat olive oil in oven-safe skillet over medium-high heat.\n7. Sear chicken for 3-4 minutes per side until golden.\n8. Transfer skillet to oven and bake 15-20 minutes until cooked through.\n9. Rest for 5 minutes, then drizzle with balsamic glaze.\n10. Serve with additional fresh basil.',
            'prep_time': 20,
            'cook_time': 25,
            'servings': 4,
            'cuisine_type': 'Italian',
            'difficulty': 'Medium'
        }
    ]
    
    try:
        for recipe_data in sample_recipes:
            recipe = Recipe.create_from_dict(recipe_data)
            db.session.add(recipe)
        
        db.session.commit()
        print(f"Successfully added {len(sample_recipes)} sample recipes to the database!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing sample data: {str(e)}")
        raise