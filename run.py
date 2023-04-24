from flask import Flask, render_template, url_for, flash, redirect, abort, request, jsonify
from datetime import datetime

from flask_admin import Admin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, DateTime, func
from wtforms import StringField, DecimalField, IntegerField, SelectField, DateTimeField
from wtforms.validators import InputRequired

from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)

# Add configuration for flask app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'  # change this to your preferred database URI
app.config['SECRET_KEY'] = "f089fcbb065ef349f60c948c962b1b981926252c9bc235598fe0508a5c4c6862"

# Initialize db
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Company(db.Model):
    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

    def __repr__(self):
        return "<Company %r" % self.name


class ProductStock(db.Model):
    __tablename__ = 'product_stock'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    price = Column(DECIMAL(10, 2))
    product_count = Column(Integer, default=1)
    company_id = Column(Integer, ForeignKey('company.id'))
    company = db.relationship("Company", backref='product')

    def __repr__(self):
        return "<Product %r>" % self.name


class InvoiceType(db.Model):
    __tablename__ = 'invoice_type'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)  # You must add only 2 values is equal to income and outcome

    def __str__(self):
        return self.name


class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = Column(Integer, primary_key=True)
    type_name = Column(String, ForeignKey('invoice_type.name'))
    type = db.relationship('InvoiceType', backref='type')
    product = Column(String(255))
    date = Column(DateTime, default=datetime.utcnow())
    product_count = Column(Integer, default=1)
    total = Column(DECIMAL(10, 2))
    company_id = Column(Integer, ForeignKey('company.id'))
    company = db.relationship("Company", backref="company")


# Create Forms for adding company and product
class CompanyForm(FlaskForm):
    name = StringField(label='Name', validators=[InputRequired()])


class ProductForm(FlaskForm):
    name = StringField(label='Name', validators=[InputRequired()])
    price = DecimalField(label="Price", validators=[InputRequired()])
    product_count = IntegerField(label="Product count")
    company_id = SelectField(label='Company', validators=[InputRequired()])


# Create Forms for incoming products and outgoing
class ProductInvoiceForm(FlaskForm):
    type = SelectField(label='Type')
    product_name = StringField(label='Product name', validators=[InputRequired()])
    date = DateTimeField(label='Date')
    product_count = IntegerField(label='Product count', validators=[InputRequired()])
    total = DecimalField(label='Total price', validators=[InputRequired()])
    company_id = SelectField(label='Company', validators=[InputRequired()])


class DateForm(FlaskForm):
    date_from = DateTimeField(label='Date From', validators=[InputRequired()])
    date_to = DateTimeField(label='Date To', validators=[InputRequired()])


def validate_time_period(date_from, date_to):
    if date_from >= date_to:
        return False
    return True


@app.route('/', methods=["GET", "POST"])
def main():
    """
    This endpoint returns main page with list of companies and products
    """
    invoices_at_time_period = None
    income_invoices_by_company = None
    outcome_invoices_by_company = None
    if request.method == "POST":
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')

        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            if not validate_time_period(date_from, date_to):
                flash('Invalid time period: start date must be before end date')
                return redirect(url_for('main'))

        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('main'))

        invoices_at_time_period = Invoice.query.filter(Invoice.date > date_from, Invoice.date < date_to).all()

        income_invoices_by_company = db.session.query(
            Company.name,
            func.sum(Invoice.total).label('total'),
            func.sum(Invoice.product_count).label('count')
        ).join(Invoice, Company.id == Invoice.company_id). \
            join(InvoiceType, Invoice.type_name == InvoiceType.name). \
            filter(InvoiceType.name == 'income'). \
            group_by(Company.name).all()
        outcome_invoices_by_company = db.session.query(
            Company.name,
            func.sum(Invoice.total).label('total'),
            func.sum(Invoice.product_count).label('count')
        ).join(Invoice, Company.id == Invoice.company_id). \
            join(InvoiceType, Invoice.type_name == InvoiceType.name). \
            filter(InvoiceType.name == 'outcome'). \
            group_by(Company.name).all()

    companies = Company.query.all()
    products = ProductStock.query.all()
    date_form = DateForm()
    return render_template('main.html',
                           companies=companies,
                           products=products,
                           form=date_form,
                           invoices=invoices_at_time_period,
                           income_invoices_by_company=income_invoices_by_company,
                           outcome_invoices_by_company=outcome_invoices_by_company)


@app.route('/company/add', methods=["GET", "POST"])
def add_company():
    """
    Form for adding company
    """
    form = CompanyForm(meta={'csrf': False})

    if form.validate_on_submit():
        name = form.name.data
        company = Company(name=name)
        db.session.add(company)
        db.session.commit()
        form.name.data = ''
        flash("Company added successfully")
        return redirect(url_for('main'))
    return render_template('add_company.html', form=form)


@app.route('/company/<int:company_id>')
def get_company(company_id: int):
    """
    This endpoint returns company by id
    """
    company = Company.query.get_or_404(company_id)
    return render_template('company.html', company=company)


@app.route('/edit/company/<int:company_id>', methods=["GET", "POST"])
def edit_company(company_id: int):
    """
    This endpoint edit company by id
    """
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(meta={'csrf': False})

    if form.validate_on_submit():
        company.name = form.name.data

        db.session.add(company)
        db.session.commit()

        flash('Company has been successfully edited')
        return redirect(url_for('get_company', company_id=company_id))

    form.name.data = ''
    return render_template('edit_company.html', company=company, form=form)


@app.route('/delete/company/<int:company_id>', methods=["GET", "POST"])
def delete_company(company_id: int):
    """
    This endpoint delete company by id
    """
    company = Company.query.get_or_404(company_id)
    # error = None

    try:
        db.session.delete(company)
        db.session.commit()

        flash('Company has been successfully deleted')
        return redirect(url_for('main'))

    except ValueError as e:
        # Return a 404 error with the exception message
        return jsonify({'error': str(e)}), 404


@app.route('/product/add', methods=["GET", "POST"])
def add_product():
    """
    Form for adding products
    """
    form = ProductForm(meta={'csrf': False})
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]

    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data

        product = ProductStock(name=name,
                               price=price,
                               product_count=form.product_count.data,
                               company_id=form.company_id.data)
        db.session.add(product)
        db.session.commit()
        form.name.data = ''
        form.price.data = ''
        form.company_id.data = ''
        flash("Product added successfully")
        return redirect(url_for('main'))
    return render_template('add_product.html', form=form)


@app.route('/edit/product/<int:product_id>', methods=["GET", "POST"])
def edit_product(product_id: int):
    """
    Form for editing product
    """
    product = ProductStock.query.get_or_404(product_id)
    form = ProductForm(meta={'csrf': False})
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.product_count = form.product_count.data
        product.company_id = form.company_id.data

        db.session.add(product)
        db.session.commit()

        flash('Product has been successfully edited')
        return redirect(url_for('get_product_by_id', product_id=product.id))

    form.name.data = ''
    form.price.data = ''
    form.product_count.data = ''
    form.company_id.data = ''

    return render_template('edit_product.html', form=form, product=product)


@app.route('/delete/product/<int:product_id>', methods=["GET", "POST"])
def delete_product(product_id: int):
    """
    This endpoint delete product by id
    """
    try:
        product = ProductStock.query.get_or_404(product_id)

        db.session.delete(product)
        db.session.commit()

        flash('Product has been successfully deleted')
        return render_template('main.html')

    except ValueError as e:
        # Return a 404 error with the exception message
        return jsonify({'error': str(e)}), 404


@app.route('/product/<int:product_id>')
def get_product_by_id(product_id: int):
    """
    This endpoint returns a product by id
    """
    product = ProductStock.query.get_or_404(product_id)
    return render_template('product.html', product=product)


@app.route('/invoice/<int:invoice_id>')
def get_invoice_by_id(invoice_id: int):
    """
    This endpoint returns an invoice by id
    """
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoice.html', invoice=invoice)


@app.route('/invoices')
def get_invoices():
    """
    This endpoint returns all invoices
    """
    invoices = Invoice.query.all()
    return render_template('invoices.html', invoices=invoices)


@app.route('/invoice/add', methods=["GET", "POST"])
def add_invoice():
    """
    Form for adding an invoice
    """
    form = ProductInvoiceForm(meta={'csrf': False})
    form.type.choices = [(t.name, t.name) for t in InvoiceType.query.all()]
    form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]

    if form.validate_on_submit():
        product_type = form.type.data
        print(product_type)

        invoice = Invoice(
            type_name=form.type.data,
            product=form.product_name.data,
            date=form.date.data,
            product_count=form.product_count.data,
            total=form.total.data,
            company_id=form.company_id.data
        )

        product_name_exist = ProductStock.query.filter_by(name=form.product_name.data).first()
        product_company_exist = ProductStock.query.filter_by(company_id=form.company_id.data)
        product_exist = product_name_exist and product_company_exist

        if product_type == 'income':  # income

            if product_exist:
                product_name_exist.product_count += form.product_count.data
                product_name_exist.price += form.total.data
                # db.session.add(product_name_exist)
                db.session.commit()
            else:
                product = ProductStock(
                    name=form.product_name.data,
                    price=form.total.data,
                    product_count=form.product_count.data,
                    company_id=form.company_id.data
                )
                db.session.add(product)
                db.session.commit()

        elif product_type == 'outcome':  # outgoing
            if not product_exist:
                abort(404, description=f"Product don`t exists at product stock")
            else:
                product_at_stock = product_name_exist.product_count
                if product_at_stock < form.product_count.data:
                    abort(404, description=f"There is no {form.product_count.data} at product stock")
                else:
                    product_name_exist.product_count -= form.product_count.data
                    product_name_exist.price -= form.total.data
                    db.session.commit()

        db.session.add(invoice)
        db.session.commit()

        form.type.data = ''
        form.product_count.data = ''
        form.total.data = ''
        form.company_id.data = ''
        form.date.data = ''

        flash('Invoice successfully added')
        return redirect(url_for('get_invoices'))

    return render_template('add_invoice.html', form=form)


@app.route('/invoice/income')
def get_income_invoice():
    """
    This endpoint returns invoices that are income
    """
    income = db.session.query(Invoice).join(InvoiceType).filter(InvoiceType.name == "income").all()
    return render_template('income_invoices.html', income=income)


@app.route('/invoice/outgoing')
def get_outgoing_invoices():
    """
    This endpoint returns invoices that are outcome
    """
    outgoing = db.session.query(Invoice).join(InvoiceType).filter(InvoiceType.name == 'outcome').all()
    return render_template('outgoing_invoices.html', outgoing=outgoing)


class CompanyModelView(ModelView):
    pass


class ProductModelView(ModelView):
    pass


admin = Admin(app)
admin.add_view(CompanyModelView(Company, db.session))
admin.add_view(ProductModelView(ProductStock, db.session))


# Create db
def create_db_if_not_exists():
    with app.app_context():
        if not db.engine.has_table(Company.__tablename__) or not db.engine.has_table(ProductStock.__tablename__) or not db.engine.has_table(InvoiceType.__tablename__) or not db.engine.has_table(Invoice.__tablename__):
            db.create_all()
            print('Database created successfully!')
            income_invoice_type = InvoiceType(name='income')
            outcome_invoice_type = InvoiceType(name='outcome')
            db.session.add_all([income_invoice_type, outcome_invoice_type])
            db.session.commit()
        else:
            print('Database already exists.')


if __name__ == "__main__":
    create_db_if_not_exists()
    app.run(debug=True)
