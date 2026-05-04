 Exactly right. That's the core thing the ORM does — it's a translator from Python expressions to SQL queries.                                
                                                                                                                                             
  ---                                                                                                                                          
  Direct one-to-one mappings you'll use constantly                                                                                             
                                                                                                                                               
  ┌───────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐                 
  │                      Django ORM                       │                     What runs in PostgreSQL                      │                 
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤                 
  │ Post.objects.all()                                    │ SELECT * FROM posts_post;                                        │                 
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤               
  │ Post.objects.filter(published=True)                   │ SELECT * FROM posts_post WHERE published = TRUE;                 │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.filter(published=True, views__gt=100)    │ SELECT * FROM posts_post WHERE published = TRUE AND views > 100; │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.get(pk=5)                                │ SELECT * FROM posts_post WHERE id = 5; (expects exactly 1 row)   │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.exclude(published=False)                 │ SELECT * FROM posts_post WHERE NOT (published = FALSE);          │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.order_by('-created_at')                  │ SELECT * FROM posts_post ORDER BY created_at DESC;               │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.count()                                  │ SELECT COUNT(*) FROM posts_post;                                 │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.filter(published=True).count()           │ SELECT COUNT(*) FROM posts_post WHERE published = TRUE;          │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.first()                                  │ SELECT * FROM posts_post LIMIT 1;                                │
  ├───────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ Post.objects.filter(...).aggregate(total=Count('id')) │ SELECT COUNT(id) AS total FROM posts_post WHERE ...;             │
  └───────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

  The pattern: .objects is your starting point. Every .filter(), .exclude(), .order_by(), .annotate() adds another clause to the SQL. The query
   doesn't actually execute until you do something that needs the result (iterate it, count it, get one, etc.) — so chaining is cheap.

  ---
  Some Django-specific operators (the __lookup syntax)

  Django uses double-underscore (__) for SQL operators that aren't simple equality:

  ┌───────────────────────────┬─────────────────────────────────────────────────────────┐
  │          Django           │                           SQL                           │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ views__gt=100             │ views > 100                                             │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ views__gte=100            │ views >= 100                                            │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ views__lt=100             │ views < 100                                             │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ created_at__year=2026     │ EXTRACT(YEAR FROM created_at) = 2026                    │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ title__icontains='django' │ title ILIKE '%django%' (case-insensitive partial match) │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ title__startswith='How'   │ title LIKE 'How%'                                       │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ id__in=[1, 2, 3]          │ id IN (1, 2, 3)                                         │
  ├───────────────────────────┼─────────────────────────────────────────────────────────┤
  │ category__isnull=True     │ category IS NULL                                        │
  └───────────────────────────┴─────────────────────────────────────────────────────────┘

  Read the __ as "on this field, apply this operator." So views__gt=100 is "on views, apply gt (greater than) with value 100." It compiles to
  views > 100.

  Joins use __ too — Post.objects.filter(category__name='Django') translates to:
  SELECT posts_post.*
  FROM posts_post
  LEFT JOIN posts_category ON posts_post.category_id = posts_category.id
  WHERE posts_category.name = 'Django';

  category__name literally means "walk the FK to category, then look at name." Same __ syntax as the operators, just doing a join instead.

  ---
  The killer trick — see the actual SQL the ORM generates

  You can inspect it directly in the shell. Open one and try:

  >>> from posts.models import Post
  >>> Post.objects.filter(published=True).query

  Output:
  SELECT "posts_post"."id", "posts_post"."title", ... FROM "posts_post"
  WHERE "posts_post"."published"

  Anytime you're wondering "what SQL does this become?" — just append .query to a queryset. Use this constantly when learning. It removes all
  mystery about what's happening under the hood.

  In Django dev environments, people also run Django Debug Toolbar which shows every SQL query a page made, with timings. Useful to spot N+1
  query bugs.

  ---
  Why ORM is worth the abstraction

  You correctly identified what ORMs do — translate Python to SQL. The advantages:

  ┌───────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
  │                          Without ORM                          │                                With ORM                                │
  ├───────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Hand-write strings: f-strings, concatenation, vulnerable to   │ Parameterization automatic, can't accidentally inject                  │
  │ injection                                                     │                                                                        │
  ├───────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Database-specific (Postgres SQL ≠ MySQL SQL)                  │ Same Python code works across PostgreSQL, MySQL, SQLite                │
  ├───────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Manage cursors/connections yourself                           │ Connection pool managed for you                                        │
  ├───────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Returns row tuples — type-mangled                             │ Returns Python objects with proper types (datetimes, decimals, FK      │
  │                                                               │ relationships)                                                         │
  ├───────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ You write joins explicitly                                    │ Walk relationships with __ (post.author.username does the join         │
  │                                                               │ automatically)                                                         │
  └───────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘

  The ORM doesn't give you anything you couldn't write in raw SQL. It gives you safer, terser, portable code that produces the same SQL you'd
  have written by hand — but without typos, injection holes, or driver boilerplate.

  When the ORM struggles (very complex analytics, hand-tuned queries) — Django lets you drop down to raw SQL anytime: Post.objects.raw("SELECT
  ..."). Best of both worlds.

  ---
  So your intuition was spot on. Every queryset is a SQL query in disguise. Get used to mentally translating both directions and the ORM stops
  feeling magical and starts feeling like a skin over SQL.

---------------

Solid plan. Here's a full side-by-side reference. Use it as a cheat sheet whenever the ORM feels foreign — every line on the right is doing  
  exactly what the line on the left does.                                                                                                      
                                                                                                                                               
  ---                                                                                                                                          
  1. SELECT — fetching rows               
                                                                                                                                               
  ┌───────────────────────────────────┬──────────────────────────────────────────────┐                                                         
  │                SQL                │                  Django ORM                  │                                                         
  ├───────────────────────────────────┼──────────────────────────────────────────────┤                                                         
  │ SELECT * FROM posts_post;         │ Post.objects.all()                           │
  ├───────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT id, title FROM posts_post; │ Post.objects.values('id', 'title')           │
  ├───────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT title FROM posts_post;     │ Post.objects.values_list('title', flat=True) │
  └───────────────────────────────────┴──────────────────────────────────────────────┘

  ---
  2. WHERE — filtering

  ┌─────────────────────────────────────────────────────┬─────────────────────────────────────────────────────┐
  │                         SQL                         │                     Django ORM                      │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE published = TRUE;    │ Post.objects.filter(published=True)                 │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE views > 100;         │ Post.objects.filter(views__gt=100)                  │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE views >= 100;        │ Post.objects.filter(views__gte=100)                 │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE views < 50;          │ Post.objects.filter(views__lt=50)                   │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE id = 5;              │ Post.objects.filter(id=5) or Post.objects.get(id=5) │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE id IN (1, 2, 3);     │ Post.objects.filter(id__in=[1, 2, 3])               │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE category_id IS NULL; │ Post.objects.filter(category__isnull=True)          │
  ├─────────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE published = FALSE;   │ Post.objects.filter(published=False)                │
  └─────────────────────────────────────────────────────┴─────────────────────────────────────────────────────┘

  AND / OR — multiple conditions

  ┌──────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────┐
  │                               SQL                                │                        Django ORM                         │
  ├──────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE published = TRUE AND views > 100; │ Post.objects.filter(published=True, views__gt=100)        │
  ├──────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE published = TRUE OR views > 100;  │ Post.objects.filter(Q(published=True) | Q(views__gt=100)) │
  ├──────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE NOT (published = FALSE);          │ Post.objects.exclude(published=False)                     │
  └──────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────┘

  (Q lets you combine conditions with | for OR, & for AND, ~ for NOT — needed only when AND isn't enough.)

  Pattern matching

  ┌───────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────┐
  │                                    SQL                                    │                   Django ORM                   │
  ├───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE title LIKE 'How%';                         │ Post.objects.filter(title__startswith='How')   │
  ├───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE title LIKE '%django%';                     │ Post.objects.filter(title__contains='django')  │
  ├───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
  │ SELECT * FROM posts_post WHERE title ILIKE '%django%'; (case-insensitive) │ Post.objects.filter(title__icontains='django') │
  └───────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────┘

  ---
  3. ORDER BY / LIMIT

  ┌────────────────────────────────────────────────────────────┬──────────────────────────────────────────────┐
  │                            SQL                             │                  Django ORM                  │
  ├────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT * FROM posts_post ORDER BY created_at DESC;         │ Post.objects.order_by('-created_at')         │
  ├────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT * FROM posts_post ORDER BY views DESC, title ASC;   │ Post.objects.order_by('-views', 'title')     │
  ├────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT * FROM posts_post LIMIT 10;                         │ Post.objects.all()[:10]                      │
  ├────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT * FROM posts_post LIMIT 10 OFFSET 20;               │ Post.objects.all()[20:30]                    │
  ├────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ SELECT * FROM posts_post ORDER BY created_at DESC LIMIT 1; │ Post.objects.order_by('-created_at').first() │
  └────────────────────────────────────────────────────────────┴──────────────────────────────────────────────┘

  The minus sign on '-created_at' = DESCENDING. No minus = ASCENDING. Same as SQL's default behavior.

  ---
  4. INSERT — creating rows

  ┌──────────────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
  │                                   SQL                                    │                         Django ORM                          │
  ├──────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
  │ INSERT INTO posts_category (name, slug) VALUES ('Django', 'django');     │ Category.objects.create(name='Django', slug='django')       │
  ├──────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
  │ INSERT INTO posts_category (name, slug) VALUES ('Django', 'django')      │ (same — .create() returns the created object)               │
  │ RETURNING *;                                                             │                                                             │
  ├──────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
  │ INSERT INTO posts_post (title, body, author_id, ...) VALUES (...);       │ Post.objects.create(title='...', body='...', author=akash,  │
  │                                                                          │ ...)                                                        │
  └──────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘

  You can also do it in two steps (closer to the Bank pattern):
  cat = Category(name='Django', slug='django')   # in memory
  cat.save()                                      # writes to DB
  Equivalent to the one-line Category.objects.create(...).

  ---
  5. UPDATE — modifying rows

  ┌──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────┐
  │                             SQL                              │                        Django ORM                        │
  ├──────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ UPDATE posts_post SET published = TRUE WHERE id = 5;         │ Post.objects.filter(id=5).update(published=True)         │
  ├──────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ UPDATE posts_post SET published = FALSE WHERE author_id = 5; │ Post.objects.filter(author_id=5).update(published=False) │
  ├──────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ UPDATE posts_post SET views = views + 1 WHERE id = 5;        │ Post.objects.filter(id=5).update(views=F('views') + 1)   │
  └──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────┘

  (F('views') is a reference to the column itself — used for atomic in-place updates. We'll use this for the view counter when we do concept
  #10.)

  ---
  6. DELETE — removing rows

  ┌─────────────────────────────────────────────────┬───────────────────────────────────────────────┐
  │                       SQL                       │                  Django ORM                   │
  ├─────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ DELETE FROM posts_post WHERE id = 5;            │ Post.objects.filter(id=5).delete()            │
  ├─────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ DELETE FROM posts_post WHERE published = FALSE; │ Post.objects.filter(published=False).delete() │
  ├─────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ DELETE FROM posts_post; (everything!)           │ Post.objects.all().delete()                   │
  └─────────────────────────────────────────────────┴───────────────────────────────────────────────┘

  ---
  7. JOINs — across tables

  This is where the ORM really shines. You walk foreign keys with __ (double underscore).

  ┌──────────────────────────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────┐
  │                                         SQL                                          │                   Django ORM                    │
  ├──────────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ SELECT p.* FROM posts_post p JOIN posts_category c ON p.category_id = c.id WHERE     │ Post.objects.filter(category__name='Django')    │
  │ c.name = 'Django';                                                                   │                                                 │
  ├──────────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ SELECT p.* FROM posts_post p JOIN auth_user u ON p.author_id = u.id WHERE u.username │ Post.objects.filter(author__username='akash')   │
  │  = 'akash';                                                                          │                                                 │
  ├──────────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ SELECT p.title, u.username FROM posts_post p JOIN auth_user u ON p.author_id = u.id; │ Post.objects.values('title',                    │
  │                                                                                      │ 'author__username')                             │
  └──────────────────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────┘

  category__name reads as: "walk the foreign key from category, look at name." Django writes the JOIN for you.

  ---
  8. AGGREGATES — summarizing the whole table

  ┌──────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┐
  │                       SQL                        │                                     Django ORM                                      │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT COUNT(*) FROM posts_post;                 │ Post.objects.count()                                                                │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT COUNT(*) FROM posts_post WHERE published  │ Post.objects.filter(published=True).count()                                         │
  │ = TRUE;                                          │                                                                                     │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT SUM(views) FROM posts_post;               │ Post.objects.aggregate(total=Sum('views')) → {'total': 47}                          │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT AVG(views) FROM posts_post;               │ Post.objects.aggregate(avg=Avg('views'))                                            │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT MAX(views) FROM posts_post;               │ Post.objects.aggregate(top=Max('views'))                                            │
  ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ SELECT COUNT(*), SUM(views), AVG(views) FROM     │ Post.objects.aggregate(total=Count('id'), total_views=Sum('views'),                 │
  │ posts_post;                                      │ avg_views=Avg('views'))                                                             │
  └──────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┘

  aggregate() returns a dict. That's exactly what you used in your /api/stats/ endpoint.

  ---
  9. GROUP BY — annotate (next concept)

  This is where annotate (the sibling of aggregate) comes in. It does GROUP BY:

  ┌──────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
  │                                 SQL                                  │                            Django ORM                            │
  ├──────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ SELECT category_id, COUNT(*) FROM posts_post GROUP BY category_id;   │ Post.objects.values('category').annotate(post_count=Count('id')) │
  ├──────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ SELECT c.id, c.name, COUNT(p.id) AS post_count FROM posts_category c │                                                                  │
  │  LEFT JOIN posts_post p ON p.category_id = c.id GROUP BY c.id,       │ Category.objects.annotate(post_count=Count('posts'))             │
  │ c.name;                                                              │                                                                  │
  └──────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

  We'll cover annotate next beat.

  ---
  10. The killer trick to verify any of this

  In the shell:

  >>> from posts.models import Post
  >>> str(Post.objects.filter(published=True).order_by('-views').query)

  Returns the SQL Django will run:
  SELECT "posts_post"."id", ..., "posts_post"."views"
  FROM "posts_post"
  WHERE "posts_post"."published"
  ORDER BY "posts_post"."views" DESC

  Use this constantly when learning. Anytime the ORM feels confusing, run it through .query and you'll see the SQL it produces. Removes all
  mystery.

  ---
  How to read any Django queryset

  The mental flow is always:

  Model.objects . filter(...)  . filter(...)  . order_by(...)  . values(...)  . count()
     ↑              ↑              ↑                ↑                ↑           ↑
   starting       WHERE          WHERE            ORDER BY        SELECT      execute
   point         (chained        (more)                          (specific
                  applies AND)                                    columns)

  Each .method() adds one SQL clause. Nothing actually runs until you do something terminal like count(), first(), list(), or iterate the
  queryset.

  ---
