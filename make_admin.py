from app import app, db, User

def make_user_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"User '{username}' is now an admin!")
        else:
            print(f"User '{username}' not found!")

if __name__ == '__main__':
    username = input("Enter username to make admin: ")
    make_user_admin(username) 

make_user_admin('Afra')