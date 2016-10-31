import os
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from urlparse import urlparse
import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

class PortalUser(ndb.Model):
	identity = ndb.StringProperty(indexed=True)
	email = ndb.StringProperty(indexed=False)
	role = ndb.StringProperty(indexed=False)

class Course(ndb.Model):
	handler = ndb.StructuredProperty(PortalUser)
	name = ndb.StringProperty(indexed=True)	

class AssignmentGive(ndb.Model):
	name = ndb.StringProperty(indexed=True)
	course = ndb.StructuredProperty(Course)
	deadline = ndb.StringProperty(indexed=False)
	max_marks = ndb.FloatProperty(indexed=False)
	question_key = ndb.BlobKeyProperty()

class AssignmentSubmit(ndb.Model):
	author = ndb.StructuredProperty(PortalUser)
	name = ndb.StringProperty(indexed=True)
	course = ndb.StructuredProperty(Course)
	date = ndb.DateTimeProperty(auto_now_add=True)
	answer_key = ndb.BlobKeyProperty()
	marks = ndb.FloatProperty(indexed=False)
	comments = ndb.StringProperty(indexed=False)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
        	check = PortalUser.query(PortalUser.identity == user.user_id())
        	if not check.get():
        		pass
        	else:
        		self.redirect('/home')
        	url = users.create_logout_url(self.request.uri)
        	url_linktext = 'Sign out'
        else:
        	url = users.create_login_url(self.request.uri)
        	url_linktext = 'Sign in or Register'
        template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'PortalUser' : PortalUser,}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class HomePage(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			ent = PortalUser.query(PortalUser.identity == user.user_id())
			res = ent.fetch(1)
			user_role = res[0].role
			if user_role == 'Teacher':
				pass
			elif user_role == 'Student':
				pass
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'user_role' : user_role,}
			template = JINJA_ENVIRONMENT.get_template('home.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')	
	def post(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			user_role = self.request.get('role')
			portal_user = PortalUser(identity=user.user_id(),email=user.email(),role=user_role)
			portal_user_key = portal_user.put()	
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'user_role' : user_role,}
			template = JINJA_ENVIRONMENT.get_template('home.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class TeacherCourse(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			course = self.request.get("course")
			assignments = []
			check = Course.query(Course.name == course)
			if check.get() and check.fetch(1)[0].handler.identity != user.user_id():
				self.redirect('/')
			else:
				if not check.get():
					co = Course()
					co.handler = PortalUser(identity=user.user_id(),email=user.email(),role='Teacher')
					co.name = course
					co.put()
				#else:
				assignment_query = AssignmentGive.query(AssignmentGive.course.handler.identity == user.user_id())
				assignments = assignment_query.fetch(10)
				for assignment in assignments:
					pass 
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'course' : course,'Course' : Course,'assignments' : assignments}
			template = JINJA_ENVIRONMENT.get_template('teacher.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class AssignmentUploadFormHandler(webapp2.RequestHandler):
    def get(self):
    	user = users.get_current_user()
    	if user:
    		url = users.create_logout_url(self.request.uri)
    		url_linktext = 'Sign out'
    		co = self.request.get("course")
        	upload_url = blobstore.create_upload_url('/upload_assignment?course=%s' %co)
        	template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'upload_url' : upload_url}
        	template = JINJA_ENVIRONMENT.get_template('assignmentgiveform.html')
        	self.response.write(template.render(template_values))
        else:
			self.redirect('/')

class AssignmentUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		upload = self.get_uploads()[0]
		course_name = self.request.get("course")
		co = Course(handler=PortalUser(identity=users.get_current_user().user_id(),email=users.get_current_user().email(),role='Teacher'),name=course_name)
		assignment = AssignmentGive(name=self.request.get('name'),course=co,deadline=self.request.get('deadline'),max_marks=float(self.request.get('maxmarks')),question_key=upload.key())
		assignment.put()
		self.redirect('/teachercourse?course=%s' %co.name)

class StudentCourse(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			co = self.request.get("course")
			this_course = Course.query(Course.name == co)
			assignments = []
			if this_course.get():
				given = AssignmentGive.query(AssignmentGive.course.name == this_course.fetch(1)[0].name)
				assignments = given.fetch(10)
				for assignment in assignments:
					pass
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'course' : this_course, 'assignments' : assignments}
			template = JINJA_ENVIRONMENT.get_template('student.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class AssignmentSubmitFormHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			co = self.request.get("course")
			upload_url = blobstore.create_upload_url('/submit_assignment?course=%s' %co)
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'upload_url' : upload_url}
			template = JINJA_ENVIRONMENT.get_template('assignmentsubmitform.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class AssignmentSubmitHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		upload = self.get_uploads()[0]
		course_name = self.request.get("course")
		auth = PortalUser(identity = users.get_current_user().user_id(), email = users.get_current_user().email(), role = 'Student')
		assignment_name = self.request.get('name')
		co = Course.query(Course.name == course_name).fetch(1)[0]
		key = upload.key()
		assignment = AssignmentSubmit(author = auth,name = assignment_name,course = co,answer_key = key,marks = -1,comments = '')
		assignment.put()
		self.redirect('/studentcourse?course=%s' %co.name)

class MyAssignments(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			co = self.request.get("course")
			assignments = AssignmentSubmit.query(AssignmentSubmit.author.identity == user.user_id() and AssignmentSubmit.course.name == co)
			results = assignments.fetch(10)
			for assignment in results:
				pass
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'course' : co,'assignments' : results}
			template = JINJA_ENVIRONMENT.get_template('myassignments.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class Answers(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			assignment = self.request.get('assignment').split()
			question = AssignmentGive.query(AssignmentGive.name == assignment[0] and AssignmentGive.course.name == assignment[1]).fetch(1)[0].question_key
			sub_query = AssignmentSubmit.query(AssignmentSubmit.name == assignment[0] and AssignmentSubmit.course.name == assignment[1])
			assignments = sub_query.fetch(1000)
			for answer in assignments:
				pass
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'assignments' : assignments,'assignment' : assignment,'question' : question}
			template = JINJA_ENVIRONMENT.get_template('answers.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class EvaluateForm(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Sign out'
			ans = self.request.get('answer').split()
			assignment_query = AssignmentSubmit.query(AssignmentSubmit.author.identity == ans[0] and AssignmentSubmit.course.name == ans[1] and AssignmentSubmit.name == ans[2])
			assignment = assignment_query.fetch(1)[0]
			template_values = {'user' : user,'url' : url,'url_linktext' : url_linktext,'assignment':assignment}
			template = JINJA_ENVIRONMENT.get_template('evaluateform.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect('/')

class EvaluateFormHandler(webapp2.RequestHandler):
	def post(self):
		assignment = self.request.get('assignment').split()
		assignment_query = AssignmentSubmit.query(AssignmentSubmit.author.identity == assignment[0] and AssignmentSubmit.course.name == assignment[1] and AssignmentSubmit.name == assignment[2])
		answer = assignment_query.fetch(1)[0]
		new_one = AssignmentSubmit(key = answer.key,author = answer.author, name = answer.name, course = answer.course,date = answer.date,answer_key = answer.answer_key,marks = float(self.request.get('marks')),comments = self.request.get('comments'))
		new_one.put()
		self.redirect('/answers?assignment=%s+%s' %(answer.name,answer.course.name))

class ViewAssignmentHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, assignment_key):
    	self.send_blob(assignment_key)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/home', HomePage),
    ('/teachercourse', TeacherCourse),
    ('/studentcourse', StudentCourse),
    ('/giveassignment', AssignmentUploadFormHandler),
    ('/upload_assignment', AssignmentUploadHandler),
    ('/view_assignment/([^/]+)?', ViewAssignmentHandler),
    ('/submitassignment', AssignmentSubmitFormHandler),
    ('/submit_assignment', AssignmentSubmitHandler),
    ('/myassignments', MyAssignments),
    ('/answers', Answers),
    ('/evaluate_assignment', EvaluateForm),
    ('/finishevaluate', EvaluateFormHandler)
], debug=True)