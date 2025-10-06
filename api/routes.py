from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from models.models import db, Recipe
from data.schemas import recipe_schema, recipes_schema, search_schema
#from search.search_engine import search

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Recipe API is running!',
        'version': '1.0'
    })

@api.route('/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes with optional filtering."""
    try:
        # Optional query parameters
        cuisine_type = request.args.get('cuisine_type')
        difficulty = request.args.get('difficulty')
        max_prep_time = request.args.get('max_prep_time', type=int)
        limit = request.args.get('limit', default=50, type=int)
        
        # Build query
        query = Recipe.query
        
        if cuisine_type:
            query = query.filter(Recipe.cuisine_type.ilike(f'%{cuisine_type}%'))
        
        if difficulty:
            query = query.filter(Recipe.difficulty == difficulty)
        
        if max_prep_time:
            query = query.filter(Recipe.prep_time <= max_prep_time)
        
        # Order by creation date (newest first) and limit
        recipes = query.order_by(Recipe.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'recipes': recipes_schema.dump(recipes),
            'total': len(recipes)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recipes', 'details': str(e)}), 500

@api.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe by ID."""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        return jsonify({'recipe': recipe_schema.dump(recipe)})
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recipe', 'details': str(e)}), 500

@api.route('/recipes', methods=['POST'])
def create_recipe():
    """Create a new recipe."""
    try:
        # Validate input data
        data = recipe_schema.load(request.json)
        
        # Check if recipe with same name already exists
        existing_recipe = Recipe.query.filter_by(name=data['name']).first()
        if existing_recipe:
            return jsonify({'error': 'A recipe with this name already exists'}), 409
        
        # Create new recipe
        recipe = Recipe.create_from_dict(data)
        db.session.add(recipe)
        db.session.commit()
        
        return jsonify({
            'message': 'Recipe created successfully',
            'recipe': recipe_schema.dump(recipe)
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create recipe', 'details': str(e)}), 500

@api.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update an existing recipe."""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        # Validate input data
        data = recipe_schema.load(request.json)
        
        # Check if another recipe with the same name exists (excluding current recipe)
        existing_recipe = Recipe.query.filter(
            Recipe.name == data['name'],
            Recipe.id != recipe_id
        ).first()
        if existing_recipe:
            return jsonify({'error': 'A recipe with this name already exists'}), 409
        
        # Update recipe
        recipe.update_from_dict(data)
        db.session.commit()
        
        return jsonify({
            'message': 'Recipe updated successfully',
            'recipe': recipe_schema.dump(recipe)
        })
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update recipe', 'details': str(e)}), 500

@api.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe."""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({'message': 'Recipe deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete recipe', 'details': str(e)}), 500

@api.route('/recipes/search', methods=['POST'])
def search_recipes():
    """Search recipes based on available ingredients."""
    try:
        # Validate search data
        search_data = search_schema.load(request.json)
        user_ingredients = search_data['ingredients']
        
        # Get all recipes and calculate match scores
        query = Recipe.query
        
        # Apply optional filters
        if search_data.get('cuisine_type'):
            query = query.filter(Recipe.cuisine_type.ilike(f'%{search_data["cuisine_type"]}%'))
        
        if search_data.get('difficulty'):
            query = query.filter(Recipe.difficulty == search_data['difficulty'])
        
        if search_data.get('max_prep_time'):
            query = query.filter(Recipe.prep_time <= search_data['max_prep_time'])
        
        recipes = query.all()
        
        # Calculate match scores and filter out recipes with no matches
        scored_recipes = []
        for recipe in recipes:
            match_score = recipe.calculate_match_score(user_ingredients)
            if match_score > 0:
                recipe_dict = recipe_schema.dump(recipe)
                recipe_dict['match_score'] = match_score
                recipe_dict['matched_ingredients'] = sum(1 for user_ing in user_ingredients 
                                                       for recipe_ing in recipe.get_ingredients_list() 
                                                       if user_ing.lower() in recipe_ing or recipe_ing in user_ing.lower())
                scored_recipes.append(recipe_dict)
        
        # Sort by match score (highest first)
        scored_recipes.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Apply limit
        limit = search_data.get('limit', 10)
        scored_recipes = scored_recipes[:limit]
        
        return jsonify({
            'recipes': scored_recipes,
            'total_matches': len(scored_recipes),
            'search_ingredients': user_ingredients
        })
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to search recipes', 'details': str(e)}), 500

@api.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing query"}), 400
    #results = search(query)
    #return jsonify(results)

@api.route('/cuisines', methods=['GET'])
def get_cuisines():
    """Get list of available cuisine types."""
    try:
        cuisines = db.session.query(Recipe.cuisine_type).distinct().all()
        cuisine_list = [c[0] for c in cuisines if c[0]]
        
        return jsonify({'cuisines': sorted(cuisine_list)})
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch cuisines', 'details': str(e)}), 500

@api.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        total_recipes = Recipe.query.count()
        cuisines_count = db.session.query(Recipe.cuisine_type).distinct().count()
        
        difficulty_stats = db.session.query(
            Recipe.difficulty, 
            db.func.count(Recipe.id)
        ).group_by(Recipe.difficulty).all()
        
        return jsonify({
            'total_recipes': total_recipes,
            'total_cuisines': cuisines_count,
            'difficulty_distribution': {diff: count for diff, count in difficulty_stats}
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats', 'details': str(e)}), 500