from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import random
import ast
import nltk
import re


app = Flask(__name__)
app.debug = True



sent_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

recipe_top10_df = pd.read_csv('archive/first_10k_top_10_rec.csv')
recipes = pd.read_csv('archive/90_k_recipe.csv')

recipes['name'] == recipes['name'].map(lambda x: re.sub(' +',' ',x))

all_recipes = recipes.copy()


all_recipes.drop(columns=['Unnamed: 0','id','recipe_id','contributor_id','nutrition','submitted','tags','steps'],inplace=True)
all_recipes['ingredients'] = recipes['ingredients'].map(lambda x: ast.literal_eval(x))

recipes.drop('Unnamed: 0',axis=1,inplace=True)
recipes.drop('id',axis=1,inplace=True)
recipes.drop('recipe_id',axis=1,inplace=True)
recipes.drop('contributor_id',axis=1,inplace=True)
recipes.drop('nutrition',axis=1,inplace=True)
recipes.drop('submitted',axis=1,inplace=True)
recipes.drop('tags',axis=1,inplace=True)
recipes.drop('steps',axis=1,inplace=True)
recipes['ingredients'] = recipes['ingredients'].map(lambda x: ast.literal_eval(x))

recipes.rename({'n_steps':'Number of steps','name':'Name'},axis='columns',inplace=True)
recipes.drop('user_id_nunique',axis=1,inplace=True)
recipes.rename({'n_ingredients':'Number of ingredients'},axis='columns',inplace=True)
recipes.rename({'rating_mean':'Average rating'},axis='columns',inplace=True)
recipes.rename({'dish_recipe':'Dish Recipe'},axis='columns',inplace=True)

recipes['Average rating'] = recipes['Average rating'].map(lambda x: round(x,1))



all_recipes['rating_mean'] = all_recipes['rating_mean'].map(lambda x: round(x,1))

recipes = recipes[:10000]


recipe_top10_df.drop(columns=['Unnamed: 0','recipe1','recipe2'],inplace=True)

def cap_word(lst):
  return [word.title() for word in lst]

def string_maker(lst):
  return ' '.join(word + ',' for word in lst)

def clean_description(string):
  if type(string) != str:
    return 'No description'
  sent = sent_tokenizer.tokenize(string)
  sent = [s.capitalize() for s in sent]
  return ' '.join(sent)



recipes['ingredients'] = recipes['ingredients'].map(cap_word)
recipes['ingredients'] = recipes['ingredients'].map(string_maker)
recipes['description'] = recipes['description'].map(clean_description)





feat = ['calories',
       'total fat', 'sugar', 'sodium', 'protien', 'saturated fat',
       'carbohydrates']
X = recipes[feat].values

ss = StandardScaler()

X = ss.fit_transform(X)

def cos_sim(name, X=X, n=5):
    index = recipes.index[(recipes['Name'] == name)][0]
    rec = X[index].reshape(1,-1)
    cs = cosine_similarity(rec, X)
    rec_index = np.argsort(cs)[0][::-1]
    ordered_df = recipes.loc[rec_index]
    ordered_df = ordered_df.drop(index)
    rec_df = ordered_df.head(n)
    orig_row = recipes.loc[[index]].rename(lambda x: 'original')
    total = pd.concat((orig_row,rec_df))
    return total

#Top 10 for each recipe based on how that dish is made

def top_n(name,n=10):
    df = recipe_top10_df[recipe_top10_df['recipe1_name'] == name].sort_values('similarity_rank')[:n]

    return df

def random_recipe():
      r = random.randint(0,len(recipes))
      return pd.DataFrame(recipes.iloc[r])

def recipe_with_ingredients(ingredients,n=5):
  r_cop = recipes.copy()
  lst = []
  for i, ig in enumerate(recipes['ingredients']):
    if ingredients.lower() in ig.lower():
        lst.append(i)

    if len(lst) == 5:
      break

  return r_cop.iloc[lst].sort_values('Average rating',ascending=False)[:n]



@app.route("/",methods=["POST","GET"])
@app.route("/home",methods=["POST","GET"])
def home():
    return render_template('home copy.html')


@app.route("/rr",methods=["POST","GET"])
def rr():
    df = random_recipe()
    return render_template('random.html',df=df)

@app.route("/ingredient",methods=["POST","GET"])
def ingredient():
    i = request.form['ing']
    df = recipe_with_ingredients(i)
    df.set_index('Name',inplace=True)
    df = df.T
    return render_template('ingredient.html',df=df)



@app.route("/similar",methods=["POST","GET"])
def similar():
    s = request.form['sim']
    try:
        df = cos_sim(s)
        df = df[['Name','ingredients']]
        recipes['Name'] == recipes['Name'].map(lambda x: re.sub(' +',' ',x))
        recipes['Name'] == recipes['Name'].map(lambda x: x.strip())
        return render_template('similar.html',df=df)
    except:
        return render_template('error.html')


@app.route("/top10",methods=["POST","GET"])
def top10():
    s = request.form['top']
    df = top_n(s)
    df.drop('cosine_similarity',axis=1,inplace=True)
    df.drop('recipe1_name',axis=1,inplace=True)
    name = f'Recipes similar to {s}'
    df.rename({'recipe2_name':name},axis='columns',inplace=True)
    if len(df) == 0:
        return render_template('error.html')
    return render_template('top10.html',df=df)

@app.route("/description",methods=["POST","GET"])
def description():
    d = request.form['des']
    df = pd.DataFrame(all_recipes[all_recipes['name'].str.contains(d)])
    df.rename({'n_steps':'Number of steps','name':'Name'},axis='columns',inplace=True)
    df.drop('user_id_nunique',axis=1,inplace=True)
    df.rename({'n_ingredients':'Number of ingredients'},axis='columns',inplace=True)
    df.rename({'rating_mean':'Average rating'},axis='columns',inplace=True)
    df.rename({'dish_recipe':'Dish Recipe'},axis='columns',inplace=True)
    df['ingredients'] = df['ingredients'].map(cap_word)
    df['ingredients'] = df['ingredients'].map(string_maker)
    df['description'] = df['description'].map(clean_description)
    try:
        df = pd.DataFrame(df.iloc[0]).T
        return render_template('description.html',df=df)
    except:
        return render_template('error.html')

@app.route("/recipesearch",methods=["POST","GET"])
def recipesearch():
    n = request.form['ne']
    df = recipes[recipes['Name'].str.contains(n)]
    try:
        df = df.iloc[:10]
        df = df.T
        return render_template('recipesearch.html',df=df)
    except:
        df = df.T
        return render_template('recipesearch.html',df=df)

if __name__ == '__main__':
    app.run(debug=True)