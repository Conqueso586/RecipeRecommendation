from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Recipe(db.Model):
    """Recipe model for storing recipe data."""
    
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer, default=30)
    cook_time = db.Column(db.Integer, default=0)
    servings = db.Column(db.Integer, default=4)
    cuisine_type = db.Column(db.String(50), default='General', index=True)
    difficulty = db.Column(db.String(20), default='Medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Recipe {self.name}>'

    def to_dict(self):
        """Convert recipe to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': [ing.strip() for ing in self.ingredients.split(',') if ing.strip()],
            'instructions': self.instructions,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'servings': self.servings,
            'cuisine_type': self.cuisine_type,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create_from_dict(cls, data):
        """Create recipe from dictionary data."""
        # Handle ingredients - convert list to comma-separated string
        ingredients = data.get('ingredients', [])
        if isinstance(ingredients, list):
            ingredients_str = ', '.join(ingredients)
        else:
            ingredients_str = str(ingredients)
        
        return cls(
            name=data.get('name', '').strip(),
            ingredients=ingredients_str,
            instructions=data.get('instructions', '').strip(),
            prep_time=int(data.get('prep_time', 30)),
            cook_time=int(data.get('cook_time', 0)),
            servings=int(data.get('servings', 4)),
            cuisine_type=data.get('cuisine_type', 'General').strip(),
            difficulty=data.get('difficulty', 'Medium').strip()
        )

    def update_from_dict(self, data):
        """Update recipe from dictionary data."""
        # Handle ingredients - convert list to comma-separated string
        if 'ingredients' in data:
            ingredients = data['ingredients']
            if isinstance(ingredients, list):
                self.ingredients = ', '.join(ingredients)
            else:
                self.ingredients = str(ingredients)
        
        # Update other fields
        for field in ['name', 'instructions', 'prep_time', 'cook_time', 'servings', 'cuisine_type', 'difficulty']:
            if field in data:
                if field in ['prep_time', 'cook_time', 'servings']:
                    setattr(self, field, int(data[field]))
                else:
                    setattr(self, field, str(data[field]).strip())
        
        self.updated_at = datetime.utcnow()

    def get_ingredients_list(self):
        """Get ingredients as a list of strings."""
        return [ing.strip().lower() for ing in self.ingredients.split(',') if ing.strip()]

    def calculate_match_score(self, user_ingredients):
        """Calculate how well this recipe matches user's available ingredients."""
        recipe_ingredients = self.get_ingredients_list()
        user_ingredients_lower = [ing.strip().lower() for ing in user_ingredients]
        
        matches = 0
        for user_ing in user_ingredients_lower:
            for recipe_ing in recipe_ingredients:
                if user_ing in recipe_ing or recipe_ing in user_ing:
                    matches += 1
                    break
        
        if len(recipe_ingredients) == 0:
            return 0
        
        return round((matches / len(recipe_ingredients)) * 100, 1)