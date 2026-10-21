part def Vehicle {
	body : PBody::Body;
	cabin : PCabin::Cabin;
	powertrain : PPowertrain::Powertrain;
}
// Body branch
package PBody {
	part def Body {
		window : PBody::PWindow::Window;
	}
	// Body window - collides with Cabin.Window and struct Window
	package PWindow {
		part def Window {

			// sensor: Window position
			// unit: percent
			position : ScalarValues::Real;
		}
	}
}
// Cabin branch
package PCabin {
	part def Cabin {
		window : PCabin::PWindow::Window;
	}
	// Cabin window - collides with Body.Window and struct Window
	package PWindow {
		part def Window {

			// actuator: Window open state
			isOpen : ScalarValues::Boolean;
		}
	}
}
// Powertrain branch
package PPowertrain {
	part def Powertrain {
		status : PPowertrain::PStatus::Status;
	}
	// Powertrain status - collides with struct Status
	package PStatus {
		part def Status {

			// sensor: Engine running state
			isRunning : ScalarValues::Boolean;
		}
	}
}
